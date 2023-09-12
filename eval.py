import wandb
import hydra
from omegaconf import DictConfig
import torch
from utils.evaluation.wrapper import eval
import logging

# TODO: discard and pass device to collate_fn
def targets2device(targets, device):
    for i in range(len(targets)): 
        for k in ['masks', 'labels', 'boxes']: 
            targets[i][k] = targets[i][k].to(device)
    return targets



@hydra.main(version_base=None, config_path='./config', config_name='base')
def run(cfg: DictConfig) -> None:
    
    # Data
    testing_dataloader = hydra.utils.instantiate(cfg.data.testing)

    # Logger
    if cfg.log: 
        wandb.init(**cfg.logger, config=cfg)
        log = wandb.log
    else: log = lambda x: None

    # Model
    model = hydra.utils.instantiate(cfg.model)
    assert cfg.model.load, 'No model to load...'
    model.load_state_dict(torch.load(cfg.model.load))
    logging.info(f'Loaded {cfg.model.load}')
    model.to(cfg.device).eval()

    eval(model, testing_dataloader, cfg.device, 
         num_batches=cfg.num_eval_batches, log=log) 


if __name__ == '__main__':
    run()