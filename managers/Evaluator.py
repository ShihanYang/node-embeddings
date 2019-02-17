import numpy as np
import torch
from sklearn.metrics.pairwise import pairwise_distances
import pdb


class Evaluator():
    def __init__(self, model, data_sampler, params):
        self.model = model
        self.data_sampler = data_sampler
        self.params = params

    # Find the rank of ground truth head in the distance array,
    # If (head, num, rel) in all_data,
    # skip without counting.
    def _argwhere(self, head, tail, rel, array, h):
        wrongAnswer = 0
        for num in array:
            if num == head * h + tail * (1 - h):
                return wrongAnswer
            elif (head * (1 - h) + num * h, num * (1 - h) + tail * h, rel) in self.data_sampler.all_data:
                continue
            else:
                wrongAnswer += 1
        return wrongAnswer

    def get_log_data(self, eval_mode='head'):
        # pdb.set_trace()

        h_e = self.model.ent_embeddings.weight.data.cpu().numpy()[self.data_sampler.data[:, 0]]
        t_e = self.model.ent_embeddings.weight.data.cpu().numpy()[self.data_sampler.data[:, 1]]
        r_e = self.model.rel_embeddings.weight.data.cpu().numpy()[self.data_sampler.data[:, 2]]

        mr = []
        hit10 = []

        if eval_mode == 'head' or eval_mode == 'avg':
            c_h_e = t_e - r_e

            distHead = pairwise_distances(c_h_e, self.model.ent_embeddings.weight.data.cpu().numpy(), metric='manhattan')

            rankArrayHead = np.argsort(distHead, axis=1)

            # Don't check whether it is false negative
            if not self.params.filter:
                rankListHead = [int(np.argwhere(elem[1] == elem[0])) for elem in zip(self.data_sampler.data[:, 0], rankArrayHead)]
            else:
                rankListHead = [int(self._argwhere(elem[0], elem[1], elem[2], elem[3], h=1))
                                for elem in zip(self.data_sampler.data[:, 0], self.data_sampler.data[:, 1],
                                                self.data_sampler.data[:, 2], rankArrayHead)]

            isHit10ListHead = [x for x in rankListHead if x < 10]

            assert len(rankListHead) == len(self.data_sampler.data)

            mr.append(np.mean(rankListHead))
            hit10.append(len(isHit10ListHead) / len(rankListHead))

# -------------------------------------------------------------------- #

        if eval_mode == 'tail' or eval_mode == 'avg':
            c_t_e = h_e + r_e

            distTail = pairwise_distances(c_t_e, self.model.ent_embeddings.weight.data.cpu().numpy(), metric='manhattan')

            rankArrayTail = np.argsort(distTail, axis=1)

            # Don't check whether it is false negative
            if not self.params.filter:
                rankListTail = [int(np.argwhere(elem[1] == elem[0])) for elem in zip(self.data_sampler.data[:, 1], rankArrayTail)]
            else:
                rankListTail = [int(self._argwhere(elem[0], elem[1], elem[2], elem[3], h=0))
                                for elem in zip(self.data_sampler.data[:, 0], self.data_sampler.data[:, 1],
                                                self.data_sampler.data[:, 2], rankArrayTail)]

            isHit10ListTail = [x for x in rankListTail if x < 10]

            assert len(rankListTail) == len(self.data_sampler.data)

            mr.append(np.mean(rankListTail))
            hit10.append(len(isHit10ListTail) / len(rankListTail))

        mr = np.mean(mr)
        hit10 = np.mean(hit10)

        log_data = dict([
            ('hit@10', hit10),
            ('mr', mr)])

        return log_data
