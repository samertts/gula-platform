{{- define "gula.name" -}}
{{- default .Chart.Name .Values.global.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "gula.fullname" -}}
{{- if .Values.global.fullnameOverride -}}
{{- .Values.global.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.global.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "gula.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "gula.labels" -}}
helm.sh/chart: {{ include "gula.chart" . }}
{{ include "gula.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: gula-platform
{{- with .Values.global.labels }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "gula.selectorLabels" -}}
app.kubernetes.io/name: {{ include "gula.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "gula.componentLabels" -}}
{{ include "gula.selectorLabels" . }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "gula.validateApplicationImageTag" -}}
{{- $tag := .Values.global.imageTag | default "" -}}
{{- if not (regexMatch "^[0-9a-fA-F]{7,64}$" $tag) -}}
{{- fail "global.imageTag must be a 7-64 character immutable hexadecimal commit SHA" -}}
{{- end -}}
{{- end -}}

{{- define "gula.image" -}}
{{- $root := .root | default . -}}
{{- $registry := $root.Values.global.imageRegistry | default "ghcr.io/samertts/gula-platform" -}}
{{- $repository := .repository | default "backend" -}}
{{- $tag := .tag | default $root.Values.global.imageTag -}}
{{- $pullPolicy := .pullPolicy | default $root.Values.global.imagePullPolicy -}}
image: "{{ $registry }}/{{ $repository }}:{{ $tag }}"
imagePullPolicy: "{{ $pullPolicy }}"
{{- end -}}

{{- define "gula.probe" -}}
{{- $probe := .probe -}}
{{- $path := .path | default "/health" -}}
{{- $port := .port | default 8000 -}}
httpGet:
  path: {{ $path }}
  port: {{ $port }}
initialDelaySeconds: {{ $probe.initialDelaySeconds | default 30 }}
periodSeconds: {{ $probe.periodSeconds | default 15 }}
timeoutSeconds: {{ $probe.timeoutSeconds | default 5 }}
failureThreshold: {{ $probe.failureThreshold | default 5 }}
successThreshold: {{ $probe.successThreshold | default 1 }}
{{- end -}}

{{- define "gula.resources" -}}
{{- with .resources -}}
resources:
  requests:
    memory: {{ .requests.memory | default "128Mi" }}
    cpu: {{ .requests.cpu | default "100m" }}
  limits:
    memory: {{ .limits.memory | default "256Mi" }}
    cpu: {{ .limits.cpu | default "500m" }}
{{- end -}}
{{- end -}}

{{- define "gula.namespace" -}}
{{- .Values.global.namespace | default "gula" -}}
{{- end -}}

{{- define "gula.topologySpreadConstraints" -}}
{{- if .constraints -}}
topologySpreadConstraints:
{{- range .constraints }}
  - maxSkew: {{ .maxSkew | default 1 }}
    topologyKey: {{ .topologyKey | default "topology.kubernetes.io/zone" }}
    whenUnsatisfiable: {{ .whenUnsatisfiable | default "DoNotSchedule" }}
    labelSelector:
      matchLabels:
        {{- with .labelSelector }}
          {{- with .matchLabels }}
            {{- range $key, $value := . }}
        {{ $key }}: {{ $value }}
            {{- end }}
          {{- else }}
        app.kubernetes.io/part-of: gula-platform
          {{- end }}
        {{- else }}
        app.kubernetes.io/part-of: gula-platform
        {{- end }}
{{- end }}
{{- end }}
{{- end -}}

{{- define "gula.envFromConfigMap" -}}
envFrom:
  - configMapRef:
      name: {{ .Values.configMap.name }}
{{- end -}}

{{- define "gula.envSecretRefs" -}}
{{- range . }}
- name: {{ .name }}
  valueFrom:
    secretKeyRef:
      name: {{ .secretRef }}
      key: {{ .key }}
{{- end -}}
{{- end -}}

{{- define "gula.imagePullSecrets" -}}
{{- with .image }}
{{- with .pullSecrets }}
imagePullSecrets:
{{- range . }}
  - name: {{ .name }}
{{- end }}
{{- end }}
{{- end }}
{{- end -}}

{{- define "gula.podSecurityContext" -}}
{{- with .Values.podSecurityContext }}
securityContext:
  runAsNonRoot: {{ .runAsNonRoot }}
  runAsUser: {{ .runAsUser }}
  runAsGroup: {{ .runAsGroup }}
  fsGroup: {{ .fsGroup }}
  fsGroupChangePolicy: {{ .fsGroupChangePolicy }}
  seccompProfile:
    type: {{ .seccompProfile.type }}
{{- end }}
{{- end -}}

{{- define "gula.containerSecurityContext" -}}
{{- with .Values.securityContext }}
securityContext:
  allowPrivilegeEscalation: {{ .allowPrivilegeEscalation }}
  capabilities:
    drop:
      {{- range .capabilities.drop }}
      - {{ . }}
      {{- end }}
  readOnlyRootFilesystem: {{ .readOnlyRootFilesystem }}
  runAsNonRoot: {{ .runAsNonRoot }}
  runAsUser: {{ .runAsUser }}
  seccompProfile:
    type: {{ .seccompProfile.type }}
{{- end }}
{{- end -}}

{{- define "gula.serviceMonitor" -}}
{{- if .enabled -}}
{{- $root := .root | default . -}}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ .name }}
  namespace: {{ $root.Values.global.namespace }}
  labels:
    {{- include "gula.labels" $root | nindent 4 }}
    release: prometheus
    {{- with .labels }}
    {{ toYaml . }}
    {{- end }}
  {{- with .annotations }}
  annotations:
    {{ toYaml . | nindent 4 }}
  {{- end }}
spec:
  selector:
    matchLabels:
      {{- include "gula.selectorLabels" $root | nindent 6 }}
      app.kubernetes.io/component: {{ .component }}
  endpoints:
    - port: {{ .port | default "http" }}
      interval: {{ .interval | default "30s" }}
      scrapeTimeout: {{ .scrapeTimeout | default "10s" }}
      path: {{ .path | default "/metrics" }}
      {{- with .parameters }}
      params:
        {{- toYaml . | nindent 8 }}
      {{- end }}
  namespaceSelector:
    matchNames:
      - {{ $.Values.global.namespace }}
{{- end }}
{{- end -}}
