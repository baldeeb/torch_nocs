from models.nocs import get_nocs_resnet50_fpn
from models.discriminator import DiscriminatorWithOptimizer
from torchvision.models.detection.mask_rcnn import MaskRCNN_ResNet50_FPN_Weights

from habitat_data_util.utils.dataset import HabitatDataloader
from torch.utils.data import DataLoader
from utils.dataset import collate_fn
from torch.optim import Adam
import torch 
from tqdm import tqdm
import wandb
import pathlib as pl
import os
from time import time

# DATA_DIR = "/home/baldeeb/Code/pytorch-NOCS/data/habitat-generated/00847-bCPU9suPUw9/metadata.json"
DATA_DIR = "/home/baldeeb/Code/pytorch-NOCS/data/habitat-generated/200of100scenes_26selectChairs"  # larger dataset

LOAD_MRCNN = None # '/home/baldeeb/Code/pytorch-NOCS/checkpoints/nocs/saved/mrcnn_2epoch.pth'


DEVICE='cuda:1'
CHKPT_PATH = pl.Path(f'/home/baldeeb/Code/pytorch-NOCS/checkpoints/nocs/{time()}')
os.makedirs(CHKPT_PATH)

def targets2device(targets, device):
    for i in range(len(targets)): 
        for k in ['masks', 'labels', 'boxes']: 
            targets[i][k] = targets[i][k].to(device)
    return targets

def run_training(model, dataloader, optimizer, num_epochs, save_prefix=''):
    for epoch in tqdm(range(num_epochs)):
        for itr, (images, targets) in enumerate(dataloader):
            images = images.to(DEVICE)
            targets = targets2device(targets, DEVICE)
            losses = model(images, targets)
            loss = sum(losses.values())
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            wandb.log(losses)
            wandb.log(nocs_discriminator.log)
            wandb.log({'loss': loss})

            # Save image and NOCS every 10 iterations
            if itr % 10 == 0: 
                with torch.no_grad():
                    model.eval()
                    r = model(images)
                    if sum([v.numel() for k, v in r[0].items()]) != 0:
                        _printable = lambda a: a.permute(1,2,0).detach().cpu().numpy()
                        wandb.log({'image': wandb.Image(_printable(images[0]))})
                        if 'nocs' in r[0]:
                            wandb.log({'nocs':wandb.Image(_printable(r[0]['nocs'][0]))})
                    model.train()
        torch.save(model.state_dict(), CHKPT_PATH/f'{save_prefix}{epoch}.pth')
        wandb.log({'epoch': epoch})


def params_generator(model, ignore=None, select=None):
    for name, param in model.named_parameters():
        if ignore and any([x in name for x in ignore]):
            continue
        if select and not any([x in name for x in select]):
            continue
        yield param


# Initialize Model
nocs_discriminator = DiscriminatorWithOptimizer(
                            in_ch = 3,
                            optim_args={'lr': 2e-4, 
                                        'betas': (0.5, 0.999)},
                        )
model = get_nocs_resnet50_fpn(
                maskrcnn_weights=MaskRCNN_ResNet50_FPN_Weights.DEFAULT,
                nocs_loss=nocs_discriminator)
model.to(DEVICE).train()

habitatdata = HabitatDataloader(DATA_DIR)
dataloader = DataLoader(habitatdata, 
                        batch_size=8, 
                        shuffle=True, 
                        collate_fn=collate_fn)

wandb.init(project="torch-nocs", name="NOCSfull_GAN")


# For traditional nocs training.
# make sure that loss is set to cross entropys.
if False:
    optimizer = Adam(model.parameters(), lr=1e-4, betas=(0.5, 0.999))
    run_training(model, dataloader, optimizer, num_epochs=2, save_prefix='normal_')
    exit(0)


# Either load a mask rcnn or train one.
if LOAD_MRCNN:
    model.load_state_dict(torch.load(LOAD_MRCNN))
    print(f'Loaded {LOAD_MRCNN}')
else:
    # Freeze nocs heads and discriminator
    model.roi_heads.ignore_nocs = True
    mrcnn_params = list(params_generator(model, ignore=['nocs_loss', 'nocs_heads']))
    optimizer = Adam(mrcnn_params, lr=1e-4, betas=(0.5, 0.999))
    run_training(model, dataloader, optimizer, num_epochs=2, save_prefix='mrcnn_')


# Only train nocs
model.roi_heads.ignore_nocs = False
mrcnn_params = list(params_generator(model, ignore=['nocs_loss', 'nocs_heads']))
for p in mrcnn_params: p.requires_grad = False
nocs_params = list(params_generator(model, select=['nocs_heads'], ignore=['nocs_loss']))
optimizer = Adam(nocs_params, lr=2e-4, betas=(0.5, 0.999))

run_training(model, dataloader, optimizer, num_epochs=10)