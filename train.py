from models.nocs import NOCS
from torchvision.models import ResNet50_Weights
from torchvision.models.detection.backbone_utils import resnet_fpn_backbone    
from torchvision.models.detection.mask_rcnn import MaskRCNN

from habitat_data_util.utils.dataset import HabitatDataloader
from torch.utils.data import DataLoader

from utils.mask_to_bbox import mask2bbox
import numpy as np
import torch

# Initialize Model
backbone = resnet_fpn_backbone('resnet50', ResNet50_Weights.DEFAULT)
# model = NOCS(backbone, 2)
model = MaskRCNN(backbone, 2)

def labels2masks(labels):
    '''Creates a mask for each label in labels'''
    masks = []
    for label in np.unique(labels):
        masks.append(labels == label)
    return np.stack(masks)



# Load data    
def collate_fn(batch):
    rgb = np.array([v[0]['image']/255.0 for v in batch])
    rgb = torch.as_tensor(rgb).permute(0, 3, 1, 2).float()
    targets = []
    for data in batch:
        images, meta = data[0], data[1]
        depth = torch.as_tensor(images['depth']).unsqueeze(1)
        boxes = torch.as_tensor(mask2bbox(images['semantics']).astype(np.int64))
        semantics = torch.as_tensor(images['semantics'].astype(np.int64)).unsqueeze(1)
        semantic_ids = torch.as_tensor([v['semantic_id'] for v in meta['objects'].values()])
        masks = torch.as_tensor(labels2masks(semantics))
        targets.append({
            'depth': depth, 'masks': masks,
            'labels': semantics, 'boxes': boxes, 
            'semantic_ids': semantic_ids,})

    return rgb, targets

habitatdata = HabitatDataloader("/home/baldeeb/Code/pytorch-NOCS/data/habitat-generated/00847-bCPU9suPUw9/metadata.json")
dataloader = DataLoader(habitatdata, batch_size=1, shuffle=True, collate_fn=collate_fn)


# for data, meta in dataloader:
#     labels = [v['semantic_id'] for v in meta['objects'].values()]
#     targets={
#         'boxes': mask2bbox(data['semantics']).astype(np.uint8),
#         'labels': data['semantics'],
#         # 'labels': meta['semantics'],
#     }

device='cuda'
def targets2device(targets, device):
    for i in range(len(targets)): 
        for k in ['masks', 'labels', 'boxes']: 
            targets[i][k] = targets[i][k].to(device)
model.train()
model.to(device)
for images, targets in dataloader:
    images = images.to(device)
    targets = targets2device(targets, device)
    predictions = model(images, targets)
    print(predictions)
    break


