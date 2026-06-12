## Generate sample with SDEdit method

First, you need to clone the environment used (github: https://github.com/javrit/anemoi-env), and place yourself in the folder to launch training/finetuning.

The key element is to use the `sdedit_scoring` runner.
The `sdedit_scoring` runner generates perturbed atmospheric states using the SDEdit method.
Starting from a real analysis state at `date`, it produces one perturbed forecast every `timestep`
up to `lead_time`. At each step, the state is **reloaded from the real analysis** (not from the
previously predicted state), and SDEdit noise is applied during the diffusion process.

---

### 1. Runner — `sdedit_scoring`

```yaml
runner:
  sdedit_scoring:               # allows to define sampling parameters
    noise_scheduler_params:     
      schedule_type: "karras"  
      sigma_max: 1000           
      sigma_min: 0.02           
      rho: 7.0                 
      num_steps: 100            # total diffusion steps
      num_steps_sdedit: 30      # number of SDEdit steps, must be <= num_steps
      SDEdit: True              # activate SDEdit method
    sampler_params:
      sampler: "heun"           
      S_churn: 2.5             
      S_min: 0.75
      S_max: 1000
      S_noise: 1.05
    condition_files:
      mean_point: path/to/mean_point.npy # same as in training
      mean_vars: path/to/mean_vars.npy # same as in training
      std_vars: path/to/std_vars.npy # same as in training
```


**`num_steps_sdedit`** controls how many diffusion steps are used for the SDEdit perturbation —
fewer steps = closer to the original analysis, more steps = more perturbed output.

### 2. Lead time and date

```yaml
lead_time: 9    
```

A perturbed state is generated every `timestep` (defined in the checkpoint) from `date`
up to `date + lead_time`. For example with `timestep=3h` and `lead_time=9h`, you get
perturbed state at t+0h, t+3h, t+6h.


### 3. outputs

2 types of output has been used : netcdf and grib.

Netcdf files are used score the model (easy to manipulate).
Grib fils are used to generate perturbed initial conditions to pass as input to a forecast model  

---

A full config example is available at ./src/anemoi/inference/gen_SDEdit_perturbed_state.yaml

---







