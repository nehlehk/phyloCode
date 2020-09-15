from dendropy import Tree, DnaCharacterMatrix
import dendropy
import myPhylo
import numpy as np
import matplotlib.pyplot as plt
import numpy.linalg as la
import logging
import hmmlearn._utils




# ==============================================   input  ==============================================================
tree_path = '/home/nehleh/Documents/0_Research/PhD/Data/simulationdata/recombination/ShortDataset/RAxML_bestTree.tree'
tree = Tree.get_from_path(tree_path, 'newick')
alignment = dendropy.DnaCharacterMatrix.get(file=open("/home/nehleh/Documents/0_Research/PhD/Data/simulationdata/recombination/ShortDataset/wholegenome.fasta"), schema="fasta")


pi = [0.2184,0.2606,0.3265,0.1946]
rates = [0.975070 ,4.088451 ,0.991465 ,0.640018 ,3.840919 ]
GTR_sample = myPhylo.GTR_model(rates,pi)

column = myPhylo.get_DNA_fromAlignment(alignment)
dna = column[0]
myPhylo.set_index(tree,dna)
tips = len(dna)

tips_num = len(alignment)
alignment_len = alignment.sequence_size


taxon = tree.taxon_namespace
nu = 0.4
# ==============================================   methods  ============================================================
class GTR_model:
    def __init__(self, rates, pi):
        self.rates = rates
        self.pi = pi
    #     ========================================================================
    def get_pi(self):
        return self.pi
    #     ========================================================================
    def p_matrix(self , br_length):
        p = np.zeros((4, 4))

        mu = 0
        freq = np.zeros((4, 4))
        q = np.zeros((4, 4))
        sqrtPi = np.zeros((4, 4))
        sqrtPiInv = np.zeros((4, 4))
        exchang = np.zeros((4, 4))
        s = np.zeros((4, 4))
        fun = np.zeros(1)
        a, b, c, d, e = self.rates
        f = 1

        freq = np.diag(self.pi)
        sqrtPi = np.diag(np.sqrt(self.pi))
        sqrtPiInv = np.diag(1.0 / np.sqrt(self.pi))
        mu = 1 / (2 * ((a * self.pi[0] * self.pi[1]) + (b * self.pi[0] * self.pi[2]) + (c * self.pi[0] * self.pi[3]) + (d * self.pi[1] * self.pi[2]) + (
                e * self.pi[1] * self.pi[3]) + (self.pi[2] * self.pi[3])))
        exchang[0][1] = exchang[1][0] = a
        exchang[0][2] = exchang[2][0] = b
        exchang[0][3] = exchang[3][0] = c
        exchang[1][2] = exchang[2][1] = d
        exchang[1][3] = exchang[3][1] = e
        exchang[2][3] = exchang[3][2] = f


        q = np.multiply(np.dot(exchang, freq), mu)

        for i in range(4):
            q[i][i] = -sum(q[i][0:4])


        s = np.dot(sqrtPi, np.dot(q, sqrtPiInv))


        eigval, eigvec = la.eig(s)
        eigvec_inv = la.inv(eigvec)

        left = np.dot(sqrtPiInv, eigvec)
        right = np.dot(eigvec_inv, sqrtPi)

        p = np.dot(left, np.dot(np.diag(np.exp(eigval * br_length)), right))


        return p


def give_index(c):
    if c == "A":
        return 0
    elif c == "C":
        return 1
    elif c == "G":
        return 2
    elif c == "T":
        return 3


def set_index(tree,dna):
    tips = len(dna)
    for node in tree.postorder_node_iter():
        node.index = 0
        node.annotations.add_bound_attribute("index")

    s = tips
    for id, node in enumerate(tree.postorder_node_iter()):
        if not node.is_leaf():
            node.index = s
            s += 1
        else:
            for idx, name in enumerate(dna):
                if idx + 1 == int(node.taxon.label):
                    node.index = idx + 1
                    break


def get_DNA_fromAlignment(alignment):

    alignment_len = alignment.sequence_size
    tips = len(alignment)
    column = []
    for l in range(alignment_len):
        col = ""
        for t in range(tips):
            col += str(alignment[t][l])
        column.append(col)

    return column


def set_tips_partial(tree, alignment):
    partial = np.zeros(((alignment_len, tips_num, 4)))
    for site in range(alignment_len):
      pos = 0
      for node in tree.postorder_node_iter():
        dna = column[site]
        if node.is_leaf():
          # print(node.index)
          i = give_index(str(dna[pos]))
          pos += 1
          partial[site,node.index,i] = 1
    return partial


def computelikelihood_mixture(tree, alignment, tip_partial, model):
    alignment_len = alignment.sequence_size
    tips = len(dna)
    partial = np.zeros(((alignment_len, (2 * tips) - 1, 4)))
    partial[:, 0:tips, :] = tip_partial
    persite_ll = []
    for site in range(alignment_len):
        for node in tree.postorder_node_iter():
            if not node.is_leaf():
                children = node.child_nodes()
                partial[site, node.index] = np.dot(model.p_matrix(children[0].edge_length),
                                                   partial[site, children[0].index])
                for i in range(1, len(children)):
                    partial[site, node.index] *= np.dot(model.p_matrix(children[i].edge_length),
                                                        partial[site, children[i].index])
        p = np.dot(partial[site, tree.seed_node.index], model.get_pi())
        persite_ll.append(np.log(p))

    return persite_ll, partial



def make_hmm_input_mixture(tree, alignment, tip_partial, model):
    sitell, partial = computelikelihood_mixture(tree, alignment, tip_partial, model)
    children = tree.seed_node.child_nodes()
    children_count = len(children)
    x = np.zeros((alignment.sequence_size, children_count * 4))
    for id, child in enumerate(children):
        # print(child.index)
        x[:, (id * 4):((id + 1) * 4)] = partial[:, child.index, :]
    return x



def update_mixture_partial(alignment,tree,node,tipdata,posterior):
  column = get_DNA_fromAlignment(alignment)

  for site in range(alignment_len):
    dna = column[site]
    my_number = give_index(dna[node.index])
    rho = give_rho(node,posterior,site,tips_num)
    for i in range(4):
      if i == my_number:
        tipdata[site,node.index,i] = 1
      else:
        tipdata[site,node.index,i] = rho

  return tipdata


def tree_evolver_rerooted(tree ,node ,nu):
    co_recom = nu/2
    if (node.edge_length is None):
       node.edge.length = 0
    node.edge.length = node.edge.length + co_recom
    recombination_tree = tree.as_string(schema="newick")

    return recombination_tree

def give_rho(node,recom_prob,site,tips_num):
  parent = node.parent_node
  if parent == tree.seed_node:
    myindex = parent.index -1
  else:
    myindex = parent.index
  # node_prob = recom_prob[myindex - tips_num][site]
  node_prob = recom_prob[site]
  rho = 1 - node_prob[0]

  return rho


def compute_logprob_phylo(X, recom_trees, model):
    n, dim = X.shape
    result = np.zeros((n, len(recom_trees)))
    for tree_id, item in enumerate(recom_trees):
        state_tree = dendropy.Tree.get(data=item, schema="newick")
        children = state_tree.seed_node.child_nodes()
        for site_id, partial in enumerate(X):
            p = np.zeros(4)
            p = np.dot(model.p_matrix(children[0].edge_length), partial[0:4])
            for i in range(1, len(children)):
                p *= np.dot(model.p_matrix(children[i].edge_length), partial[i * 4:(i + 1) * 4])
            # result[site_id, tree_id] = sum(p)
            # print(p)
            site_l = np.dot(p, model.get_pi())
            result[site_id, tree_id] = np.log(site_l)
    return result


_log = logging.getLogger(__name__)


class phyloLL_HMM(hmmlearn.base._BaseHMM):
    def __init__(self, n_components, trees, model):
        super().__init__(n_components)
        self.trees = trees
        self.model = model

    def _init(self, X, lengths):

        """Initializes model parameters prior to fitting.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            Feature matrix of individual samples.
            n_samples == number of alignment sites
            n_features == 12: 4 site partials for each of 3 neighbour nodes

        lengths : array-like of integers, shape (n_sequences, )
            Lengths of the individual sequences in ``X``. The sum of
            these should be ``n_samples``.
        """
        init = 1. / self.n_components
        if 's' in self.init_params or not hasattr(self, "startprob_"):
            self.startprob_ = np.full(self.n_components, init)
        if 't' in self.init_params or not hasattr(self, "transmat_"):
            self.transmat_ = np.full((self.n_components, self.n_components), init)
        n_fit_scalars_per_param = self._get_n_fit_scalars_per_param()
        n_fit_scalars = sum(n_fit_scalars_per_param[p] for p in self.params)
        if X.size < n_fit_scalars:
            _log.warning("Fitting a model with {} free scalar parameters with "
                         "only {} data points will result in a degenerate "
                         "solution.".format(n_fit_scalars, X.size))

    #     ==========================================================================
    def _check(self):
        """Validates model parameters prior to fitting.

        Raises
        ------

        ValueError
            If any of the parameters are invalid, e.g. if :attr:`startprob_`
            don't sum to 1.
        """
        self.startprob_ = np.asarray(self.startprob_)
        if len(self.startprob_) != self.n_components:
            raise ValueError("startprob_ must have length n_components")
        if not np.allclose(self.startprob_.sum(), 1.0):
            raise ValueError("startprob_ must sum to 1.0 (got {:.4f})"
                             .format(self.startprob_.sum()))

        self.transmat_ = np.asarray(self.transmat_)
        if self.transmat_.shape != (self.n_components, self.n_components):
            raise ValueError(
                "transmat_ must have shape (n_components, n_components)")
        if not np.allclose(self.transmat_.sum(axis=1), 1.0):
            raise ValueError("rows of transmat_ must sum to 1.0 (got {})"
                             .format(self.transmat_.sum(axis=1)))

    #     ==========================================================================
    def _compute_log_likelihood(self, X):
        """Computes per-component log probability under the model.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            Feature matrix of individual samples.

        Returns
        -------
        logprob : array, shape (n_samples, n_components)def give_rho(node,recom_prob,site,tips_num):
  parent = node.parent_node
  if parent == tree.seed_node:
    myindex = parent.index -1
  else:
    myindex = parent.index
  # node_prob = recom_prob[myindex - tips_num][site]
  node_prob = recom_prob[site]
  rho = 1 - node_prob[0]

  return rho
            Log probability of each sample in ``X`` for each of the
            model states.
        """

        return compute_logprob_phylo(X, self.trees, self.model)

#     ==========================================================================





mytree = []
posterior = []
hiddenStates = []
score = []
tipdata = set_tips_partial(tree, alignment)
for id_tree, target_node in enumerate(tree.postorder_internal_node_iter(exclude_seed_node=True)):
    print(target_node.index)
    recombination_trees = []
    mytree.append(Tree.get_from_path(tree_path, 'newick'))
    set_index(mytree[id_tree], dna)

    # ----------- Step 1 : Make input for hmm ------------------------------------------------------
    # --------------  Stetp 1.1 : re-root the tree based on the target node where the target node is each internal node of the tree.

    mytree[id_tree].reroot_at_node(target_node, update_bipartitions=False, suppress_unifurcations=True)
    recombination_trees.append(mytree[id_tree].as_string(schema="newick"))

    # --------------  Step 1.2: Calculate X based on this re-rooted tree

    X = make_hmm_input_mixture(mytree[id_tree], alignment, tipdata, GTR_sample)
    print(X.shape)

    # ----------- Step 2: make 3 recombination trees -----------------------------------------------
    temptree = {}

    for id, child in enumerate(target_node.child_node_iter()):
        # print(child.index)
        temptree["tree{}".format(id)] = Tree.get_from_path(tree_path, 'newick')
        set_index(temptree["tree{}".format(id)], dna)

        filter_fn = lambda n: hasattr(n, 'index') and n.index == target_node.index
        target_node_temp = temptree["tree{}".format(id)].find_node(filter_fn=filter_fn)
        temptree["tree{}".format(id)].reroot_at_node(target_node_temp, update_bipartitions=False,
                                                     suppress_unifurcations=True)

        filter_fn = lambda n: hasattr(n, 'index') and n.index == child.index
        recombined_node = temptree["tree{}".format(id)].find_node(filter_fn=filter_fn)
        recombination_trees.append(tree_evolver_rerooted(temptree["tree{}".format(id)], recombined_node, nu))

    # ----------- Step 3: Call phyloHMM ----------------------------------------------------------
    model = phyloLL_HMM(n_components=4, trees=recombination_trees, model=GTR_sample)
    model.startprob_ = np.array([0.79, 0.07, 0.07, 0.07])
    model.transmat_ = np.array([[0.997, 0.001, 0.001, 0.001],
                                [0.00098, 0.999, 0.00001, 0.00001],
                                [0.00098, 0.00001, 0.999, 0.00001],
                                [0.00098, 0.00001, 0.00001, 0.999]])

    posterior.append(model.predict_proba(X))
    hiddenStates.append(model.predict(X))
    score.append(model.score(X))

    tree_updatePartial = Tree.get_from_path(tree_path, 'newick')
    set_index(tree_updatePartial, dna)
    filter_fn = lambda n: hasattr(n, 'index') and n.index == target_node.index
    target_node_partial = tree_updatePartial.find_node(filter_fn=filter_fn)
    for id, child in enumerate(target_node_partial.child_node_iter()):
        if child.is_leaf():
            # print("my beloved child:", child.index)
            new_partial = update_mixture_partial(alignment, tree_updatePartial, child, tipdata, posterior)

    print(new_partial)