import numpy as np
from utils.evaluation.tools import compute_mAP,compute_ap_from_matches_scores

class MAPConfig:
    def __init__(self, synset_names, config_dict):
        self.synset_names = synset_names
        self.num_classes = len(synset_names)
        self.degree_thresholds = range(
            config_dict.get('degree_thresholds_start'), 
            config_dict.get('degree_thresholds_end'), 
            config_dict.get('degree_thresholds_step')
        )
        self.shift_thresholds = np.linspace(
            config_dict.get('shift_thresholds_start'), 
            config_dict.get('shift_thresholds_end'), 
            config_dict.get('shift_thresholds_steps')
        ) * config_dict.get('shift_thresholds_multiplier')
        self.iou_3d_thresholds = np.linspace(
            config_dict.get('iou_3d_thresholds_start'), 
            config_dict.get('iou_3d_thresholds_end'), 
            config_dict.get('iou_3d_thresholds_steps')
        )
        self.degree_thres_list = list(self.degree_thresholds) + [360]
        self.num_degree_thres = len(self.degree_thres_list)

        self.shift_thres_list = list(self.shift_thresholds) + [100]
        self.num_shift_thres = len(self.shift_thres_list)

        self.iou_thres_list = list(self.iou_3d_thresholds)
        self.num_iou_thres = len(self.iou_thres_list)

        self.iou_3d_aps = np.zeros((self.num_classes + 1, self.num_iou_thres))
        self.iou_pred_matches_all = [np.zeros((self.num_iou_thres, 0)) for _ in range(self.num_classes)]
        self.iou_pred_scores_all  = [np.zeros((self.num_iou_thres, 0)) for _ in range(self.num_classes)]
        self.iou_gt_matches_all   = [np.zeros((self.num_iou_thres, 0)) for _ in range(self.num_classes)]
        
        self.pose_aps = np.zeros((self.num_classes + 1, self.num_degree_thres, self.num_shift_thres))
        self.pose_pred_matches_all = [np.zeros((self.num_degree_thres, self.num_shift_thres, 0)) for _  in range(self.num_classes)]
        self.pose_gt_matches_all  = [np.zeros((self.num_degree_thres, self.num_shift_thres, 0)) for _  in range(self.num_classes)]
        self.pose_pred_scores_all = [np.zeros((self.num_degree_thres, self.num_shift_thres, 0)) for _  in range(self.num_classes)]
        self.use_matches_for_pose = config_dict.get('use_matches_for_pose')
        self.iou_pose_thres = config_dict.get('iou_pose_thres')
        self.print_result=config_dict.get('print_result')


    def computing_mAP(self, result, target, device):
        # Implement the logic to compute mAP using result and target
        compute_mAP(result,target,device,self.synset_names,self.iou_thres_list,self.iou_pred_matches_all,self.iou_pred_scores_all,
                                self.iou_gt_matches_all,self.use_matches_for_pose,self.iou_pose_thres,self.degree_thres_list, 
                                self.shift_thres_list,self.pose_pred_matches_all,self.pose_pred_scores_all,self.pose_gt_matches_all)
                    
    def display_mAP(self,log_results):
        iou_dict = {}
        iou_dict['thres_list'] = self.iou_thres_list
        for cls_id in range(1, self.num_classes):
            class_name = self.synset_names[cls_id]
            for s, iou_thres in enumerate(self.iou_thres_list):
                self.iou_3d_aps[cls_id, s] = compute_ap_from_matches_scores(self.iou_pred_matches_all[cls_id][s, :],
                                                                    self.iou_pred_scores_all[cls_id][s, :],
                                                                    self.iou_gt_matches_all[cls_id][s, :])    

        self.iou_3d_aps[-1, :] = np.mean(self.iou_3d_aps[1:-1, :], axis=0)
        
        iou_dict['aps'] = self.iou_3d_aps

        for i, degree_thres in enumerate(self.degree_thres_list):                
            for j, shift_thres in enumerate(self.shift_thres_list):
                for cls_id in range(1, self.num_classes):
                    cls_pose_pred_matches_all = self.pose_pred_matches_all[cls_id][i, j, :]
                    cls_pose_gt_matches_all = self.pose_gt_matches_all[cls_id][i, j, :]
                    cls_pose_pred_scores_all = self.pose_pred_scores_all[cls_id][i, j, :]

                    self.pose_aps[cls_id, i, j] = compute_ap_from_matches_scores(cls_pose_pred_matches_all, 
                                                                            cls_pose_pred_scores_all, 
                                                                            cls_pose_gt_matches_all)

                self.pose_aps[-1, i, j] = np.mean(self.pose_aps[1:-1, i, j])
        

        if(self.print_result):
            print('3D IoU at 25: {:.1f}'.format(self.iou_3d_aps[-1, self.iou_thres_list.index(0.25)] * 100))
            print('3D IoU at 50: {:.1f}'.format(self.iou_3d_aps[-1, self.iou_thres_list.index(0.5)] * 100))
            print('5 degree, 5cm: {:.1f}'.format(self.pose_aps[-1, self.degree_thres_list.index(5), self.shift_thres_list.index(5)] * 100))
            print('5 degree, 10cm: {:.1f}'.format(self.pose_aps[-1, self.degree_thres_list.index(5), self.shift_thres_list.index(10)] * 100))
            print('10 degree, 5cm: {:.1f}'.format(self.pose_aps[-1, self.degree_thres_list.index(10), self.shift_thres_list.index(5)] * 100))
            print('10 degree, 10cm: {:.1f}'.format(self.pose_aps[-1, self.degree_thres_list.index(10), self.shift_thres_list.index(10)] * 100))
            print('15 degree, 5cm: {:.1f}'.format(self.pose_aps[-1, self.degree_thres_list.index(15), self.shift_thres_list.index(5)] * 100))
            print('15 degree, 10cm: {:.1f}'.format(self.pose_aps[-1, self.degree_thres_list.index(15), self.shift_thres_list.index(10)] * 100))

        log_results["3D IoU at 25"] = self.iou_3d_aps[-1, self.iou_thres_list.index(0.25)] * 100
        log_results["3D IoU at 50"] = self.iou_3d_aps[-1, self.iou_thres_list.index(0.5)] * 100
        log_results["5 degree, 5cm"] = self.pose_aps[-1, self.degree_thres_list.index(5), self.shift_thres_list.index(5)] * 100
        log_results["5 degree, 10cm"] = self.pose_aps[-1, self.degree_thres_list.index(5), self.shift_thres_list.index(10)] * 100
        log_results["10 degree, 5cm"] = self.pose_aps[-1, self.degree_thres_list.index(10), self.shift_thres_list.index(5)] * 100
        log_results["10 degree, 10cm"] = self.pose_aps[-1, self.degree_thres_list.index(10), self.shift_thres_list.index(10)] * 100
        log_results["15 degree, 5cm"] = self.pose_aps[-1, self.degree_thres_list.index(15), self.shift_thres_list.index(5)] * 100
        log_results["15 degree, 10cm"] = self.pose_aps[-1, self.degree_thres_list.index(15), self.shift_thres_list.index(10)] * 100
