HOURS = 730

# Estimated Frankfurt on-demand/usage rates in USD; replace with AWS Calculator/API quote before procurement.
rates = {
    "m5.xlarge": 0.2300,
    "c5.xlarge_spot": 0.0700,
    "db.r6g.xlarge": 0.2150,
    "cache.r6g.large": 0.2060,
    "eks_cluster": 0.1000,
    "nat_gateway_hour": 0.0520,
    "nat_gateway_gb": 0.0520,
    "alb_hour": 0.0252,
    "alb_lcu_hour": 0.0080,
    "ebs_gp3_gib_month": 0.0960,
    "rds_storage_gib_month": 0.1150,
    "s3_gib_month": 0.0230,
    "public_ipv4_hour": 0.0050,
}

# Terraform desired capacity: 1 system + 2 application on-demand; 1 spot node.
compute = {
    "EKS system nodes": 1 * rates["m5.xlarge"] * HOURS,
    "EKS application nodes": 2 * rates["m5.xlarge"] * HOURS,
    "EKS spot node": 1 * rates["c5.xlarge_spot"] * HOURS,
    "EKS control plane": rates["eks_cluster"] * HOURS,
}

data = {
    "RDS instance": rates["db.r6g.xlarge"] * HOURS,
    "RDS allocated storage 500 GiB": 500 * rates["rds_storage_gib_month"],
    "ElastiCache 2 nodes": 2 * rates["cache.r6g.large"] * HOURS,
    "EBS node disks 250 GiB": 250 * rates["ebs_gp3_gib_month"],
    "S3/logs/backups 500 GiB assumption": 500 * rates["s3_gib_month"],
}

network = {
    "NAT gateway fixed": rates["nat_gateway_hour"] * HOURS,
    "NAT processing 1 TB assumption": 1000 * rates["nat_gateway_gb"],
    "ALB fixed": rates["alb_hour"] * HOURS,
    "ALB 1 LCU average": rates["alb_lcu_hour"] * HOURS,
    "Public IPv4 3 addresses assumption": 3 * rates["public_ipv4_hour"] * HOURS,
}

# Terraform enables CloudTrail, Config, GuardDuty, Security Hub, WAF, KMS and monitoring.
# These are workload/volume-sensitive and are modeled as a range, not a false point estimate.
security_monitoring_range = (150.0, 400.0)

for name, section in [("compute", compute), ("data", data), ("network", network)]:
    print(name)
    for key, value in section.items():
        print(f"  {key}: ${value:,.2f}/month")
    print(f"  subtotal: ${sum(section.values()):,.2f}/month")

base = sum(compute.values()) + sum(data.values()) + sum(network.values())
print(f"base_without_security_monitoring: ${base:,.2f}/month")
print(f"estimated_total_low: ${base + security_monitoring_range[0]:,.2f}/month")
print(f"estimated_total_high: ${base + security_monitoring_range[1]:,.2f}/month")
print(f"annual_low: ${(base + security_monitoring_range[0]) * 12:,.2f}/year")
print(f"annual_high: ${(base + security_monitoring_range[1]) * 12:,.2f}/year")

# Alternative right-sized standby scenario: one app node, one cache node, db.r6g.large at 50% of xlarge rate.
rightsized = {
    "EKS system node": 1 * rates["m5.xlarge"] * HOURS,
    "EKS application node": 1 * rates["m5.xlarge"] * HOURS,
    "EKS spot node": 1 * rates["c5.xlarge_spot"] * HOURS,
    "EKS control plane": rates["eks_cluster"] * HOURS,
    "RDS db.r6g.large approximation": 0.5 * rates["db.r6g.xlarge"] * HOURS,
    "RDS storage 500 GiB": 500 * rates["rds_storage_gib_month"],
    "ElastiCache one node": rates["cache.r6g.large"] * HOURS,
    "EBS 150 GiB": 150 * rates["ebs_gp3_gib_month"],
    "S3/logs/backups 500 GiB": 500 * rates["s3_gib_month"],
    "NAT fixed": rates["nat_gateway_hour"] * HOURS,
    "NAT processing 1 TB": 1000 * rates["nat_gateway_gb"],
    "ALB fixed+1LCU": rates["alb_hour"] * HOURS + rates["alb_lcu_hour"] * HOURS,
    "Public IPv4 3": 3 * rates["public_ipv4_hour"] * HOURS,
}
rightsized_base = sum(rightsized.values())
print(f"rightsized_base_without_security_monitoring: ${rightsized_base:,.2f}/month")
print(f"rightsized_total_low: ${rightsized_base + security_monitoring_range[0]:,.2f}/month")
print(f"rightsized_total_high: ${rightsized_base + security_monitoring_range[1]:,.2f}/month")
