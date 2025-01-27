
import dask
from dask.distributed import Client
import os
import time

nersc_instructions = """
1. Start a compute node: salloc -N 2 -n 64 -t 30 -C cpu
2. On the compute node, start dask: ./launch_workers_nersc.sh

launch_workers_nersc.sh can be found in the analysis directory.
"""

def get_client(client_type: str="dirac", scaling: int=5, scheduler_options: dict={"port": 8786}) -> Client:

    if client_type == "dirac":
        from dask_dirac import DiracCluster
        cluster = DiracCluster(cores=1, memory='0.5GB', scheduler_options=scheduler_options)
        cluster.scale(jobs=scaling)
        client = Client(cluster)

    elif client_type == "nersc":
        #scheduler_file = os.path.join(os.environ["SCRATCH"], "scheduler_file.json")
        scheduler_file = "scheduler_file.json"
        # check if file exists
        if not os.path.isfile(scheduler_file):
            print(f"Scheduler file {scheduler_file} does not exist. Instructions start NERSC jobs are...")
            print(nersc_instructions)

            # wait until file is created
            while not os.path.isfile(scheduler_file):
                time.sleep(120)
            raise FileNotFoundError(f"Scheduler file {scheduler_file} does not exist.")

        dask.config.config["distributed"]["dashboard"]["link"] = "{JUPYTERHUB_SERVICE_PREFIX}proxy/{host}:{port}/status" 
        client = Client(scheduler_file=scheduler_file)

    elif client_type == "local":
        from dask.distributed import LocalCluster
        cluster = LocalCluster()
        cluster.scale(jobs=scaling)
        client = Client(cluster)

    else:
        raise ValueError(f"Unsupported client type: {client_type}")
    
    return client