from kubernetes import client, config
import os
import time
import datetime
import boto3

# Load Kubernetes configuration
config.load_kube_config()

# Set the namespace and directory to save logs
namespace = "logsupload"
local_directory = "/home/jasbir/kuberneteslogtos3/logs"

# AWS S3 configurations
bucket_name = "k8logstos3"
s3_prefix = "kubernetes-logs/"

# Create Kubernetes API client
core_api = client.CoreV1Api()

# Create an S3 client
s3_client = boto3.client('s3')

# Function to save logs to a file
def save_logs(pod_name, container_name, log_file):
    logs = core_api.read_namespaced_pod_log(name=pod_name, namespace=namespace, container=container_name)
    with open(log_file, "a") as f:
        f.write(logs)

# Function to upload logs to S3
def upload_logs_to_s3():
    for root, dirs, files in os.walk(local_directory):
        for file in files:
            file_path = os.path.join(root, file)
            s3_key = os.path.join(s3_prefix, os.path.relpath(file_path, local_directory))
            s3_client.upload_file(file_path, bucket_name, s3_key)

# Function to collect logs from all pods in the namespace
def collect_logs():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    for pod in core_api.list_namespaced_pod(namespace=namespace).items:
        pod_name = pod.metadata.name
        for container in pod.spec.containers:
            container_name = container.name
            log_file = os.path.join(local_directory, f"{pod_name}_{container_name}.log")
            save_logs(pod_name, container_name, log_file)

# Main loop to collect logs every 5 seconds
while True:
    collect_logs()
    time.sleep(5)
    upload_logs_to_s3()  # Upload logs to S3 after collecting them locally
