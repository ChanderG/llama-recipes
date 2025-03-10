# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

import inspect
from dataclasses import asdict
from peft import (
    LoraConfig,
    AdaptionPromptConfig,
    PrefixTuningConfig,
)

from llama_recipes.configs import (datasets,
                                   lora_config,
                                   llama_adapter_config,
                                   prefix_config,
                                   train_config,
                                   aim_config,  # Aim tracker config
                                  )

from llama_recipes.utils.dataset_utils import DATASET_PREPROC

def update_config(config, **kwargs):
    if isinstance(config, (tuple, list)):
        for c in config:
            update_config(c, **kwargs)
    else:
        for k, v in kwargs.items():
            if hasattr(config, k):
                setattr(config, k, v)
            elif "." in k:
                # allow --some_config.some_param=True
                config_name, param_name = k.split(".")
                if type(config).__name__ == config_name:
                    if hasattr(config, param_name):
                        setattr(config, param_name, v)
                    else:
                        # In case of specialized config we can warm user
                        print(f"Warning: {config_name} does not accept parameter: {k}")
            elif isinstance(config, train_config):
                print(f"Warning: unknown parameter {k}")

def generate_dict_from_configs(config):
    # Convert the config objects to dictionaries, 
    # converting all values to strings to ensure they can be serialized
    return {k: str(v) for k, v in vars(config).items() if not k.startswith('__') and not callable(v)}

def generate_peft_config(train_config, kwargs):
    configs = (lora_config, llama_adapter_config, prefix_config)
    peft_configs = (LoraConfig, AdaptionPromptConfig, PrefixTuningConfig)
    names = tuple(c.__name__.rstrip("_config") for c in configs)
    
    assert train_config.peft_method in names, f"Peft config not found: {train_config.peft_method}"
    
    config = configs[names.index(train_config.peft_method)]()
    
    update_config(config, **kwargs)
    params = asdict(config)
    peft_config = peft_configs[names.index(train_config.peft_method)](**params)
    
    return peft_config

def generate_dataset_config(train_config, kwargs):
    names = tuple(DATASET_PREPROC.keys())

    assert train_config.dataset in names, f"Unknown dataset: {train_config.dataset}"
    
    dataset_config = {k:v for k, v in inspect.getmembers(datasets)}[train_config.dataset]()
        
    update_config(dataset_config, **kwargs)
    
    return dataset_config

def generate_tracker_config(train_config, kwargs):
    if train_config.tracker is None:
        return None

    configs = (aim_config)
    names = tuple(c.__name__.rstrip("_config") for c in configs)

    assert train_config.tracker in names, f"Unknown tracker: {train_config.tracker}"

    tracker_config = configs[names.index(train_config.tracker)]()

    update_config(tracker_config, **kwargs)
    return tracker_config