from hazan import *
from hazan_penalties import *
import pdb
import time

def test1():
    """
    Do a simple test of the Bounded Trace Solver on function
    f(x)  = -\sum_k x_kk^2 defined above.

    Now do a dummy optimization problem. The
    problem we consider is

        max - sum_k x_k^2
        subject to
            sum_k x_k = 1

    The optimal solution is -1/n, where
    n is the dimension.
    """
    # dimension of square matrix X
    dims = [1,4,16,64]
    for dim in dims:
        print("dim = %d" % dim)
        # Note that H(-f) = 2 I (H is the hessian of f)
        Cf = 2.
        N_iter = 2 * dim
        b = BoundedTraceSDPHazanSolver()
        X = b.solve(neg_sum_squares, grad_neg_sum_squares,
                dim, N_iter, Cf=Cf)
        fX = neg_sum_squares(X)
        print("\tTr(X) = %f" % np.trace(X))
        print("\tf(X) = %f" % fX)
        print("\tf* = %f" % (-1./dim))
        print("\t|f(X) - f*| = %f" % (np.abs(fX - (-1./dim))))
        print("\tError Tolerance 1/%d = %f" % (N_iter, 1./N_iter))
        assert np.abs(fX - (-1./dim)) < 1./N_iter
        print("\tError Tolerance Acceptable")

def simple_equality_constraint_test(N_iter, penalty, grad_penalty):
    """
    Check that the bounded trace implementation can handle low dimensional
    equality type constraints for the given penalty function.

    With As and bs as below, we solve the problem

        max penalty(X)
        subject to
          x_11 + 2 x_22 == 1.5
          Tr(X) = x_11 + x_22 == 1.

    We should find penalty(X) >= -eps, and that the above constraints have
    a solution
    """
    m = 0
    n = 1
    dim = 2
    eps = 1./N_iter
    M = 1.
    if m + n > 0:
        M = 0.
        if m > 0:
            M += np.max((np.log(m), 1.))/eps
        if n > 0:
            M += np.max((np.log(n), 1.))/(eps**2)
    def f(X):
        return penalty(X, m, n, M, As, bs, Cs, ds, dim)
    def gradf(X):
        return grad_penalty(X, m, n, M, As, bs, Cs, ds, dim)
    As = []
    bs = []
    Cs = [np.array([[ 1.,  0.],
                    [ 0.,  2.]])]
    ds = [1.5]
    run_experiment(f, gradf, dim, N_iter)

def test2():
    """
    Check equality constraints for log_sum_exp constraints
    """
    N_iter = 50
    simple_equality_constraint_test(N_iter, log_sum_exp_penalty,
            log_sum_exp_grad_penalty)

def test3():
    """
    Check equality constraints for neg_max constraints
    """
    N_iter = 50
    simple_equality_constraint_test(N_iter, neg_max_penalty,
            neg_max_grad_penalty)

def test4():
    """
    Check that the bounded trace implementation can handle equality and
    inequality type constraints

    With As and bs as below, we solve the problem

        max penalty(X)
        subject to
            x_11 + 2 x_22 <= 1
            x_11 + 2 x_22 + 2 x_33 == 5/3
            Tr(X) = x_11 + x_22 + x_33 == 1
    """
    m = 1
    n = 1
    dim = 3
    N_iter = 50
    eps = 1./N_iter
    M = 1.
    if m + n > 0:
        M = 0.
        if m > 0:
            M += np.max((np.log(m), 1.))/eps
        if n > 0:
            M += np.max((np.log(n), 1.))/(eps**2)
        print("M", M)
    def f(X):
        return penalty(X, m, n, M, As, bs, Cs, ds)
    def gradf(X):
        return grad_penalty(X, m, n, M, As, bs, Cs, ds, dim)
    As = [np.array([[ 1., 0., 0.],
                    [ 0., 2., 0.],
                    [ 0., 0., 0.]])]
    bs = [1.]
    Cs = [np.array([[ 1.,  0., 0.],
                    [ 0.,  2., 0.],
                    [ 0.,  0., 2.]])]
    ds = [5./3]
    run_experiment(f, gradf, dim, N_iter)

def test5():
    """
    Check that the bounded trace implementation can handle equality and
    inequality type constraints with neg_max_penalty

    With As and bs as below, we solve the problem

        max neg_max_penalty(X)
        subject to
            x_11 + 2 x_22 <= 1
            x_11 + 2 x_22 + 2 x_33 == 5/3
            Tr(X) = x_11 + x_22 + x_33 == 1
    """
    m = 1
    n = 1
    dim = 3
    N_iter = 50
    eps = 1./N_iter
    M = 1.
    if m + n > 0:
        M += np.max((np.log(m), 1.))/eps
        print("M", M)
    def f(X):
        return neg_max_penalty(X, m, n, M, As, bs, Cs, ds, dim)
    def gradf(X):
        return neg_max_grad_penalty(X, m, n, M, As, bs, Cs, ds, dim, eps)
    As = [np.array([[ 1., 0., 0.],
                    [ 0., 2., 0.],
                    [ 0., 0., 0.]])]
    bs = [1.]
    Cs = [np.array([[ 1.,  0., 0.],
                    [ 0.,  2., 0.],
                    [ 0.,  0., 2.]])]
    ds = [5./3]
    run_experiment(f, gradf, dim, N_iter)

def test6():
    """
    Stress test the bounded trace solver for
    inequalities.

    With As and bs as below, we solve the probelm

    max neg_max_penalty(X)
    subject to
        x_ii <= 1/2n
        Tr(X) = x_11 + x_22 + ... + x_nn == 1

    The optimal solution should equal a diagonal matrix with small entries
    for the first n-1 diagonal elements, but a large element (about 1/2)
    for the last element.
    """
    dims = [50]
    for dim in dims:
        m = dim - 1
        n = 0
        N_iter = 1000
        eps = 1./N_iter
        M = 1.
        if m + n > 0:
            M = np.max((np.log(m+n), 1.))/eps
            print("M", M)
        def f(X):
            return neg_max_penalty(X, m, n, M, As, bs, Cs, ds, dim)
        def gradf(X):
            return neg_max_grad_penalty(X, m, n, M,
                        As, bs, Cs, ds, dim,eps)
        As = []
        for i in range(dim-1):
            Ai = np.zeros((dim,dim))
            Ai[i,i] = 1
            As.append(Ai)
        bs = []
        for i in range(dim-1):
            bi = 1./(2*dim)
            bs.append(bi)
        Cs = []
        ds = []
        run_experiment(f, gradf, dim, N_iter)

def test7():
    """
    Stress test the bounded trace solver for equalities.

    With As and bs as below, we solve the probelm

    max neg_max_penalty(X)
    subject to
        x_ii == 0, i < n
        Tr(X) = x_11 + x_22 + ... + x_nn == 1

    The optimal solution should equal a diagonal matrix with zero entries
    for the first n-1 diagonal elements, but a 1 for the diagonal element.
    """
    dims = [20]
    for dim in dims:
        m = 0
        n = dim - 1
        N_iter = 1000
        eps = 1./N_iter
        M = 1.
        if m + n > 0:
            M = np.max((np.log(m+n), 1.))/eps
            print "M", M
        def f(X):
            return neg_max_penalty(X, m, n, M, As, bs, Cs, ds, dim)
        def gradf(X):
            return neg_max_grad_penalty(X, m, n, M,
                        As, bs, Cs, ds, dim,eps)
        As = []
        bs = []
        Cs = []
        for j in range(dim-1):
            Cj = np.zeros((dim,dim))
            Cj[j,j] = 1
            Cs.append(Cj)
        ds = []
        for j in range(dim-1):
            dj = 0.
            ds.append(dj)
        run_experiment(f, gradf, dim, N_iter)

def test8():
    """
    Stress test the bounded trace solver for both equalities and
    inequalities.

    With As and bs as below, we solve the probelm

    max neg_max_penalty(X)
    subject to
        x_ij == 0, i != j
        x11
        Tr(X) = x_11 + x_22 + ... + x_nn == 1

    The optimal solution should equal a diagonal matrix with zero entries
    for the first n-1 diagonal elements, but a 1 for the diagonal element.
    """
    dims = [50]
    np.set_printoptions(precision=2)
    for dim in dims:
        m = dim - 2
        n = dim**2 - dim
        As = []
        N_iter = 1000
        eps = 1./N_iter
        M = 1.
        if m + n > 0:
            M = np.max((np.log(m+n), 1.))/eps
            print "M", M
        def f(X):
            return neg_max_penalty(X, m, n, M, As, bs, Cs, ds, dim)
        def gradf(X):
            return neg_max_grad_penalty(X, m, n, M,
                        As, bs, Cs, ds, dim,eps)
        for j in range(1,dim-1):
            Aj = np.zeros((dim,dim))
            Aj[j,j] = 1
            As.append(Aj)
        bs = []
        for j in range(1,dim-1):
            bj = 1./N_iter
            bs.append(bj)
        Cs = []
        for i in range(dim):
            for j in range(dim):
                if i != j:
                    Ci = np.zeros((dim,dim))
                    Ci[i,j] = 1
                    Cs.append(Ci)
        ds = []
        for i in range(dim):
            for j in range(dim):
                if i != j:
                    dij = 0.
                    ds.append(dij)
        run_experiment(f, gradf, dim, N_iter)

def run_experiment(f, gradf, dim, N_iter):
    eps = 1./N_iter
    B = BoundedTraceSDPHazanSolver()
    start = time.clock()
    X = B.solve(f, gradf, dim, N_iter, DEBUG=False)
    elapsed = (time.clock() - start)
    fX = f(X)
    print "\tX:\n", X
    print "\tf(X) = %f" % fX
    FAIL = (fX < -eps)
    print "\tFAIL: " + str(FAIL)
    print "\tComputation Time (s): ", elapsed


if __name__ == "__main__":
    #test1()
    #test2()
    test3()
    #test5()
    #test6()
    #test7()
    #test8()
