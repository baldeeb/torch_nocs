import pathlib as pl
from tqdm import tqdm

import wandb

import hydra
from omegaconf import DictConfig, OmegaConf

import torch

from utils.load_save import load_nocs
from utils.evaluation.wrapper import eval


# TODO: discard and pass device to collate_fn
def targets2device(targets, device):
    for i in range(len(targets)): 
        for k in ['masks', 'labels', 'boxes']: 
            targets[i][k] = targets[i][k].to(device)
    return targets



@hydra.main(version_base=None, config_path='./config', config_name='base')
def run(cfg: DictConfig) -> None:

    if 'eval' not in cfg.run_name: # add it as prefix
        cfg.run_name = f'eval_{cfg.run_name}'
    
    # Data
    testing_dataloader = hydra.utils.instantiate(cfg.data.testing)

    # Logger
    if cfg.log: 
        wandb.init(project=cfg.project_name, name=cfg.run_name, config=cfg)
        log = wandb.log
    else: log = lambda x: None

    # Model
    model = hydra.utils.instantiate(cfg.model)
    assert cfg.model.load, 'No model to load...'
    model.load_state_dict(torch.load(cfg.model.load))
    print(f'Loaded {cfg.model.load}')  # TODO: log this in a better way
    model.to(cfg.device).eval()

    eval(model, testing_dataloader, cfg.device, log=log) 


if __name__ == '__main__':
    run()