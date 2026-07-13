from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.engineering.generators.base import BaseGenerator, GenerateResult


@dataclass
class GitHubActionsSpec:
    name: str
    python_version: str = "3.11"
    on: list[str] = field(default_factory=lambda: ["push", "pull_request"])
    branches: list[str] = field(default_factory=lambda: ["main"])
    jobs: list[str] = field(default_factory=lambda: ["lint", "test", "build"])
    docker_registry: str = ""
    extra_steps: list[str] = field(default_factory=list)


class GitHubActionsGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        spec = kwargs.get("spec", kwargs.get("actions"))
        if isinstance(spec, dict):
            spec = GitHubActionsSpec(**spec)
        if spec is None:
            spec = GitHubActionsSpec(name=kwargs.get("name", "ci"))

        branch_filter = ""
        if "push" in spec.on:
            for b in spec.branches:
                branch_filter += f"\n      branches: [{b!r}]"

        on_block = f"""on:
  {chr(10).join(f"  {event}:{branch_filter}" if event == "push" and spec.branches else f"  {event}:" for event in spec.on)}"""

        jobs: dict[str, str] = {}
        if "lint" in spec.jobs:
            jobs["lint"] = self._lint_job(spec)
        if "test" in spec.jobs:
            jobs["test"] = self._test_job(spec)
        if "build" in spec.jobs:
            jobs["build"] = self._build_job(spec)

        job_names = list(jobs.keys())
        needs: dict[str, list[str]] = {}
        for i, jn in enumerate(job_names):
            if i > 0:
                needs[jn] = [job_names[i - 1]]

        needs_block = ""
        for jn, deps in needs.items():
            needs_block += f"\n      needs: {deps}"

        jobs_block = ""
        for jn in job_names:
            j = jobs[jn]
            n = needs.get(jn, [])
            needs_str = f"\n    needs: {n}" if n else ""
            jobs_block += f"""
  {jn}:{needs_str}
    runs-on: ubuntu-latest
    steps:{j}
"""

        extra_steps_block = ""
        if spec.extra_steps:
            for step in spec.extra_steps:
                extra_steps_block += f"      - run: {step}\n"

        content = f"""name: {spec.name}

{on_block}

concurrency:
  group: ${{{{ github.workflow }}}}-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:{jobs_block}{extra_steps_block}"""

        self._write(".github/workflows/ci.yml", content)
        return self._result

    def _lint_job(self, spec: GitHubActionsSpec) -> str:
        return f"""
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '{spec.python_version}'
      - run: pip install ruff
      - run: ruff check --select=E9,F821 .
"""

    def _test_job(self, spec: GitHubActionsSpec) -> str:
        return f"""
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '{spec.python_version}'
      - run: pip install pytest
      - run: python -m pytest -x --tb=short -q
"""

    def _build_job(self, spec: GitHubActionsSpec) -> str:
        steps = f"""
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '{spec.python_version}'
      - run: pip install build
      - run: python -m build"""
        if spec.docker_registry:
            steps += """
      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: """ + spec.docker_registry + """
      - run: docker build -t """ + spec.docker_registry + """/${{ github.repository }}:${{ github.sha }} .
      - run: docker push """ + spec.docker_registry + """/${{ github.repository }}:${{ github.sha }}"""
        return steps


class DockerGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        name = kwargs.get("name", "app")
        python_version = kwargs.get("python_version", "3.11-slim")
        port = kwargs.get("port", 8000)
        entrypoint = kwargs.get("entrypoint", "uvicorn app.main:app --host 0.0.0.0 --port {port}")
        use_multi_stage = kwargs.get("multi_stage", False)

        if use_multi_stage:
            content = f"""FROM python:{python_version} AS builder

WORKDIR /build
COPY pyproject.toml .
RUN pip install --user --no-warn-script-location .

FROM python:{python_version}-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ app/

ENV PATH=/root/.local/bin:$PATH

EXPOSE {port}

CMD ["{entrypoint.format(port=port)}"]
"""
        else:
            content = f"""FROM python:{python_version}

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .

EXPOSE {port}

CMD ["{entrypoint.format(port=port)}"]
"""

        self._write("Dockerfile", content)
        return self._result


class ComposeGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        services = kwargs.get("services", {})
        if not services:
            services = {
                "app": {
                    "build": ".",
                    "port": "8000:8000",
                    "depends_on": ["db", "redis"],
                },
                "db": {
                    "image": "postgres:16-alpine",
                    "port": "5432:5432",
                    "env": {"POSTGRES_DB": "app", "POSTGRES_PASSWORD": "secret"},
                    "volumes": ["pgdata:/var/lib/postgresql/data"],
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "port": "6379:6379",
                },
            }

        services_block = ""
        for name, svc in services.items():
            build = svc.get("build")
            image = svc.get("image")
            port = svc.get("port")
            env = svc.get("env", {})
            deps = svc.get("depends_on", [])
            vols = svc.get("volumes", [])

            svc_lines = [f"  {name}:"]
            if build:
                svc_lines.append(f"    build: {build}")
            if image:
                svc_lines.append(f"    image: {image}")
            if port:
                svc_lines.append(f'    ports:')
                svc_lines.append(f'      - "{port}"')
            if deps:
                svc_lines.append(f"    depends_on:")
                for d in deps:
                    svc_lines.append(f"      - {d}")
            if env:
                svc_lines.append(f"    environment:")
                for k, v in env.items():
                    svc_lines.append(f'      {k}: "{v}"')
            if vols:
                svc_lines.append(f"    volumes:")
                for v in vols:
                    svc_lines.append(f"      - {v}")
            services_block += "\n".join(svc_lines) + "\n"

        volume_names = []
        for name, svc in services.items():
            for v in svc.get("volumes", []):
                vol_name = v.split(":")[0]
                if vol_name and vol_name == vol_name.lower() and "\\" not in vol_name:
                    volume_names.append(vol_name)

        volumes_block = ""
        if volume_names:
            volumes_block = "\nvolumes:\n" + "\n".join(f"  {v}:" for v in sorted(set(volume_names)))

        content = f"""services:
{services_block}{volumes_block}
"""
        self._write("docker-compose.yml", content)
        return self._result


class KubernetesGenerator(BaseGenerator):
    def generate(self, **kwargs: Any) -> GenerateResult:
        name = kwargs.get("name", "app")
        image = kwargs.get("image", "app:latest")
        replicas = kwargs.get("replicas", 3)
        port = kwargs.get("port", 8000)
        namespace = kwargs.get("namespace", "default")
        include_postgres = kwargs.get("postgres", False)
        include_redis = kwargs.get("redis", False)

        self._ensure_dir("k8s")

        self._write("k8s/namespace.yaml", f"""apiVersion: v1
kind: Namespace
metadata:
  name: {namespace}
""")

        self._write("k8s/deployment.yaml", f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: {namespace}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
        - name: {name}
          image: {image}
          ports:
            - containerPort: {port}
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: {name}-secrets
                  key: database_url
          livenessProbe:
            httpGet:
              path: /health/live
              port: {port}
          readinessProbe:
            httpGet:
              path: /health/ready
              port: {port}
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
""")

        self._write("k8s/service.yaml", f"""apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: {namespace}
spec:
  selector:
    app: {name}
  ports:
    - port: {port}
      targetPort: {port}
  type: ClusterIP
""")

        self._write("k8s/hpa.yaml", f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {name}
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {name}
  minReplicas: {replicas}
  maxReplicas: {replicas * 3}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
""")

        if include_postgres:
            self._write("k8s/postgres.yaml", """apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: """ + namespace + """
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_DB
              value: app
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: password
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: """ + namespace + """
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
""")

        if include_redis:
            self._write("k8s/redis.yaml", """apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: """ + namespace + """
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: """ + namespace + """
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
""")

        self._write("k8s/kustomization.yaml", f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: {namespace}
resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
  - hpa.yaml
""")

        return self._result
