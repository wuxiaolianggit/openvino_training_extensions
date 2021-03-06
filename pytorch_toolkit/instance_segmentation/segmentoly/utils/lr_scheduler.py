"""
 Copyright (c) 2019 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from bisect import bisect_right

from torch.optim.lr_scheduler import _LRScheduler


class MultiStepLRWithWarmUp(_LRScheduler):
    def __init__(self,
                 optimizer,
                 milestones,
                 warmup_iters,
                 warmup_method='linear',
                 warmup_factor_base=0.33,
                 gamma=0.1,
                 last_epoch=-1):
        if warmup_method not in {'constant', 'linear'}:
            raise KeyError('Unknown warm up method: {}'.format(warmup_method))
        self.milestones = sorted(milestones)
        self.gamma = gamma
        self.warmup_iters = warmup_iters
        self.warmup_method = warmup_method
        self.warmup_factor_base = warmup_factor_base
        # Base class calls method `step` which increases `last_epoch` by 1 and then calls
        # method `get_lr` with this value. If `last_epoch` is not equal to -1, we drop
        # the first step, so to avoid this dropping do small fix by subtracting 1
        if last_epoch > -1:
            last_epoch = last_epoch - 1
        elif last_epoch < -1:
            raise ValueError('Learning rate scheduler got incorrect parameter last_epoch = {}'.format(last_epoch))
        super(MultiStepLRWithWarmUp, self).__init__(optimizer, last_epoch)

    def get_lr(self):
        # During warm up change learning rate on every step according to warmup_factor
        if self.last_epoch < self.warmup_iters:
            if self.warmup_method == 'constant':
                warmup_factor = self.warmup_factor_base
            elif self.warmup_method == 'linear':
                alpha = self.last_epoch / self.warmup_iters
                warmup_factor = self.warmup_factor_base * (1 - alpha) + alpha
            return [base_lr * warmup_factor for base_lr in self.base_lrs]
        # On the last step of warm up set learning rate equal to base LR
        elif self.last_epoch == self.warmup_iters:
            return [base_lr for base_lr in self.base_lrs]
        # After warm up increase LR according to defined in `milestones` values of steps
        else:
            return [base_lr * self.gamma ** bisect_right(self.milestones, self.last_epoch)
                    for base_lr in self.base_lrs]

    def __repr__(self):
        format_string = self.__class__.__name__ + \
                        '[warmup_method = {}, warmup_factor_base = {}, warmup_iters = {},' \
                        ' milestones = {}, gamma = {}]'.format(self.warmup_method, self.warmup_factor_base,
                                                               self.warmup_iters, str(list(self.milestones)),
                                                               self.gamma)
        return format_string
