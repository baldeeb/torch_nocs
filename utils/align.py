''' Copied from NOCS aligning.py with some cleaning and edits. '''

import numpy as np
import time

from utils.aligning import estimateSimilarityTransform

def backproject(depth, intrinsics, instance_mask):
    intrinsics_inv = np.linalg.inv(intrinsics)

    non_zero_mask = (depth > 0)
    final_instance_mask = np.logical_and(instance_mask, non_zero_mask)
    
    idxs = np.where(final_instance_mask)
    grid = np.array([idxs[1], idxs[0]])

    # shape: height * width
    length = grid.shape[1]
    ones = np.ones([1, length])
    uv_grid = np.concatenate((grid, ones), axis=0) # [3, num_pixel]

    xyz = intrinsics_inv @ uv_grid # [3, num_pixel]
    xyz = np.transpose(xyz) #[num_pixel, 3]

    z = depth[idxs[0], idxs[1]]

    pts = xyz * z[:, np.newaxis]/xyz[:, -1:]
    pts[:, 0] = -pts[:, 0]
    pts[:, 1] = -pts[:, 1]

    return pts, idxs


def align(masks :np.ndarray, 
          coords:np.ndarray, 
          depth:np.ndarray, 
          intrinsic:np.ndarray, 
          if_norm=False, with_scale=True):
    ''' Alings a bounding box to all detections in an image.
    The first index of each of coords, masks, and depth is expected to indicate the 
    number of instances that is being processed.
    Args: 
        masks of shape [B, H, W]
        coords of shape [B, C, H, W]
        depth [H, W] associated with the image that is the source of the detection.
        intrinsic [3, 3]
        if_norm ******
        with_scale ******
        '''
    num_instances = masks.size(0)
    if num_instances == 0:
        return np.zeros((0, 4, 4)), np.ones((0, 3)), elapses

    elapses = np.zeros(elapses)
    RTs = np.zeros((num_instances, 4, 4))
    bbox_scales = np.ones((num_instances, 3))
    
    for i in range(num_instances):
        # mask = masks[:, :, i]
        # coord = coords[:, :, i, :]

        result = align_sample(masks[:, :, i], 
                              coords[:, :, i, :], 
                              depth, intrinsic, 
                              if_norm=if_norm, 
                              with_scale=with_scale)
        RTs[i, :, :], bbox_scales[i, :], elapses[i] = result 
        
        # abs_coord_pts = np.abs(coord[mask==1] - 0.5)
        # bbox_scales[i, :] = 2 * np.amax(abs_coord_pts, axis=0)

        # pts, idxs = backproject(depth, intrinsic, mask)
        # coord_pts = coord[idxs[0], idxs[1], :] - 0.5

        # if if_norm:
        #     scale = np.linalg.norm(bbox_scales[i, :])
        #     bbox_scales[i, :] /= scale
        #     coord_pts /= scale

        # start = time.time()
        
        # scales, rotation, translation, _ = estimateSimilarityTransform(coord_pts, pts, False)

        # aligned_RT = np.zeros((4, 4), dtype=np.float32) 
        # if with_scale:
        #     aligned_RT[:3, :3] = np.diag(scales) / 1000 @ rotation.transpose()
        # else:
        #     aligned_RT[:3, :3] = rotation.transpose()
        # aligned_RT[:3, 3] = translation / 1000
        # aligned_RT[3, 3] = 1
        
        # elapses[i] = time.time() - start

        # # from camera world to computer vision frame
        # z_180_RT = np.zeros((4, 4), dtype=np.float32)
        # z_180_RT[:3, :3] = np.diag([-1, -1, 1])
        # z_180_RT[3, 3] = 1

        # RTs[i, :, :] = z_180_RT @ aligned_RT 


    return RTs, bbox_scales, elapses



def align_sample(mask, coord, depth, intrinsic, if_norm=False, with_scale=True):
    abs_coord_pts = np.abs(coord[mask==1] - 0.5)
    bbox_scale = 2 * np.amax(abs_coord_pts, axis=0)
    pts, idxs = backproject(depth, intrinsic, mask)
    coord_pts = coord[idxs[0], idxs[1], :] - 0.5

    if if_norm:
        scale = np.linalg.norm(bbox_scale)
        bbox_scale /= scale
        coord_pts /= scale

    start = time.time()
    scales, rotation, translation, _ = estimateSimilarityTransform(coord_pts, pts, False)
    aligned_RT = np.zeros((4, 4), dtype=np.float32) 
    if with_scale:
        aligned_RT[:3, :3] = np.diag(scales) / 1000 @ rotation.transpose()
    else:
        aligned_RT[:3, :3] = rotation.transpose()
    aligned_RT[:3, 3] = translation / 1000
    aligned_RT[3, 3] = 1
    dt = time.time() - start

    # from camera world to computer vision frame
    z_180_RT = np.zeros((4, 4), dtype=np.float32)
    z_180_RT[:3, :3] = np.diag([-1, -1, 1])
    z_180_RT[3, 3] = 1

    RTs = z_180_RT @ aligned_RT 

    RTs, bbox_scale, dt