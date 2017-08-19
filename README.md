This is a basic implementation of the Kubernetes CronJob spec. It is intended
to be used temporarily on clusters where alpha resources cannot be enabled,
such as GKE until CronJobs exit
[alpha](https://github.com/kubernetes/kubernetes/issues/41039).

# Usage

1. Create the third party `CronJob` resource on your cluster.

    ```kubectl apply -f https://raw.githubusercontent.com/tdickman/kubernetes-cron/0.1.3/cron-job-resource.yaml```

2. Run the kubernetes-cron deployment on your cluster (in the default namespace).

    ```kubectl apply -f https://raw.githubusercontent.com/tdickman/kubernetes-cron/0.1.3/deployment.yaml```

3. Create a CronJob object in your cluster based on the
   [spec](https://kubernetes.io/docs/user-guide/cron-jobs/), with one
exception. Change apiVersion to `epicconstructions.com/v1alpha1`. An example
can be found in `example-cron-job.yaml`.

# Details

This project consists of the following pieces:

* A [3rd party](https://kubernetes.io/docs/user-guide/thirdpartyresources/)
  cronjob resource that allows the creation of cronjob items in your cluster.
* A kubernetes-cron pod watches for new cronjobs, and creates child jobs based
  on the cron interval specified.


# Known Limitations
* There is no automated cleanup process to delete old jobs, which may result in
  performance issues with cronjobs that run frequently.
* SSL certs are not properly verified when connecting to the API.
* This is intended to loosely follow the alpha CronJob spec. Please open an
  issue if any issues are found.
