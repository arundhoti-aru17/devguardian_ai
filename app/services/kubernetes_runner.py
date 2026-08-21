import subprocess


class KubernetesRunner:
    """
    Runner responsible for collecting information
    from a Kubernetes cluster.
    """

    def __init__(self):
        self.context = "kind-devguardian"

    def run_command(self, command):
        """
        Run a kubectl command and return its output.
        """

        result = subprocess.run(
            [
                "kubectl",
                "--context",
                self.context,
                *command,
            ],
            capture_output=True,
            text=True,
        )

        return result.stdout + result.stderr

    def get_pods(self):
        """
        Get the current Kubernetes Pods.
        """

        return self.run_command(
            [
                "get",
                "pods",
                "-o",
                "wide",
            ]
        )
        
    def describe_pod(self, pod_name):
        """
        Get detailed information about a Kubernetes Pod.
        """

        return self.run_command(
            [
                "describe",
                "pod",
                pod_name,
            ]
        )   
        
    def get_logs(self, pod_name):
        """
        Get application logs from a Kubernetes Pod.
        """

        return self.run_command(
            [
                "logs",
                pod_name,
            ]
        )   