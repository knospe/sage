r"""
Moment-angle complexes

AUTHORS:

- Ognjen Petrov (2023-06-25)

This module implements the basic structure of moment-angle complexes.
Given a simplicial complex `K`, with a set of vertices
`V = \{v_1, v_2, \dotso, v_n\}`, a moment-angle complex over `K` is a
topological space `Z`, which is a union of `X_{\sigma}`, where
`\sigma \in K`, and `X_{\sigma} = Y_{v_1} \times Y_{v_2} \times \dotso \times Y_{v_n}`
and `Y_{v_i}` is a 2-disk (a 2-simplex) if `v_i \in \sigma`, or a 1-sphere otherwise.

.. MATH::

    Y_{v_i} =
    \begin{cases}
        D^2, &v_i \in \sigma\\
        S^1, &v_i \notin \sigma
    \end{cases}

.. NOTE::

    The mentioned union is not a disjoint union of topological spaces. The unit disks
    and the unit spheres are considered subsets of `\CC`, so the union is just
    a normal union of subsets of `\CC^n`.

They are one of the main topics of resarch in fields such as algebraic and
toric topology, as well as combinatorial algebraic geometry.

Here we moment-angle complexes as cubical complexes and try to compute mostly
things which would not require computing the moment-angle complex itself,
but rather work with the corresponding simplicial complex.

.. NOTE::

    One of the more useful properties will be the
    :meth:`bigraded Betti numbers<sage.topology.simplicial_complex.bigraded_betti_numbers>`,
    and the underlying theorem which makes this possible is Hochter's formula, which
    can be found on page 104 of :arxiv:`Toric topoloogy<1210.2368>`.

EXAMPLES::

    sage: MomentAngleComplex([[1,2,3], [2,4], [3,4]])
    Moment-angle complex over a simplicial complex with vertex set (1, 2, 3, 4) and facets {(2, 4), (3, 4), (1, 2, 3)}
    sage: X = SimplicialComplex([[0,1], [1,2], [1,3], [2,3]])
    sage: Z = MomentAngleComplex(X); Z
    Moment-angle complex over a simplicial complex with vertex set (0, 1, 2, 3) and facets {(0, 1), (1, 2), (1, 3), (2, 3)}
    sage: M = MomentAngleComplex([[1], [2]]); M
    Moment-angle complex over a simplicial complex with vertex set (1, 2) and facets {(1,), (2,)}

We can perform a number of operations, such as find the dimension or compute the homology::

    sage: M.homology()
    {0: 0, 1: 0, 2: 0, 3: Z}
    sage: Z.dimension()
    6
    sage: Z.homology()
    {0: 0, 1: 0, 2: 0, 3: Z x Z, 4: Z, 5: Z, 6: Z}
"""

# ****************************************************************************
#       Copyright (C) 2013 Ognjen Petrov <ognjenpetrov@yahoo.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from sage.misc.cachefunc import cached_method
from sage.homology.homology_group import HomologyGroup
from sage.rings.integer_ring import ZZ
from sage.rings.rational_field import QQ
from sage.structure.sage_object import SageObject
from sage.structure.unique_representation import UniqueRepresentation
from .cubical_complex import CubicalComplex, cubical_complexes
from .simplicial_complex import SimplicialComplex, copy
from .simplicial_complex_examples import Sphere, Simplex
from itertools import combinations

#TODO's:
# - Documentation (examples and tests)
# - add literature and references to bibliography!!!
# - add latex_name parameter?
# - add moment_angle_complex to simplicial_complex
# - add a method simplicial_complex()?
# - use different UniqueRepresentation complexes for components?


#Future TODO's:
# - explicitly state the vertices for construction
# - polyhedral products and real moment-angle complexes
# - golod decomposition
# - return for odd dimensional simplicial complexes in golod_decomposition?

# maybe make private?
def union(c1, c2):
    """
    Return the union of cubical complexes.

    This method returns a cubical complex whose set of maximal faces
    is the union of sets of maximal faces of ``c1`` and ``c2``.

    INPUT:

    - ``c1`` -- a cubical complex

    - ``c2`` -- a cubical complex

    OUTPUT: the union of cubical complexes ``c1`` and ``c2``

    .. WARNING::

        This is regular union, not disjoint union. One should be careful
        with the nomenclature of the vertices.

    EXAMPLES::

        sage: from sage.topology.moment_angle_complex import union
        sage: C1 = CubicalComplex([([0,0], [2,3]), ([0,1], [3,3]), ([0,1], [2,2]), ([1,1], [2,3])]); C1
        Cubical complex with 4 vertices and 8 cubes
        sage: C2 = CubicalComplex([([0,0], [2,3]), ([0,1], [3,3]), ([0,1], [2,2]), ([2,2], [2,3])]); C2
        Cubical complex with 6 vertices and 10 cubes
        sage: union(C1, C2)
        Cubical complex with 6 vertices and 11 cubes
        sage: union(C1, C1) == C1
        True
    """
    facets = []
    for f in c1.maximal_cells():
        facets.append(f)
    for f in c2.maximal_cells():
        facets.append(f)
    return CubicalComplex(facets)

class MomentAngleComplex(SageObject, UniqueRepresentation):
    r"""
    Define a moment-angle complex.

    INPUT:

    - ''simplicial_complex'' -- an instance of ''SimplicialComplex'',
      or an object from which an instance of ''SimplicialComplex'' can be
      created (e.g., list of facets), which represents the associated
      simplicial complex over which this moment-angle complex is created.

    EXAMPLES::

    If the associated simplicial_complex is an `n`-simplex, then the
    corresponding moment-angle complex is a polydisc (a complex ball) of
    complex dimension `n+1`::

        sage: Z = MomentAngleComplex([[0, 1, 2]]); Z
        Moment-angle complex over a simplicial complex with vertex set (0, 1, 2) and facets {(0, 1, 2)}

    This can be seen by viewing the components used in the construction
    of this moment-angle complex by calling ``components()``::

        sage: Z.components()
        {(0, 1, 2): [The 2-simplex, The 2-simplex, The 2-simplex]}

    If the associated simplicial_complex is a disjoint union of 2 points,
    then the corresponding moment-angle complex is homeomorphic to a boundary
    of a 3-sphere::

        sage: Z = MomentAngleComplex([[0], [1]]); Z
        Moment-angle complex over a simplicial complex with vertex set (0, 1) and facets {(0,), (1,)}
        sage: dict(sorted(Z.components().items()))
        {(0,): [The 2-simplex, Minimal triangulation of the 1-sphere],
         (1,): [Minimal triangulation of the 1-sphere, The 2-simplex]}

    The moment-angle complex passes all the tests of the test suite relative
    to its category::

        sage: TestSuite(Z).run()
    """

    def __init__(self, simplicial_complex):
        """
        Define a moment-angle complex. See :class:`MomentAngleComplex`
        for full documentation.

        TESTS::

            sage: Z = MomentAngleComplex([[0,1,2], [1,2,3], [0, 3]])
            sage: Z
            Moment-angle complex over a simplicial complex with vertex set (0, 1, 2, 3) and facets {(0, 3), (0, 1, 2), (1, 2, 3)}
            sage: dim(Z)
            7
            sage: TestSuite(Z).run()
        """
        # The underlying simplicial complex
        self._simplicial_complex = copy(simplicial_complex)
        # The moment-angle complex as a cubical complex
        # if create_complex() is called, this is computed
        self._moment_angle_complex = None
        # A dictionary of components indexed by facets
        self._components = {}

        vertices = self._simplicial_complex.vertices()
        # it suffices to perform union only over facets
        for facet in self._simplicial_complex.maximal_faces():
            Y = []
            for j in vertices:
                if j in facet:
                    Y.append(Simplex(2))
                else:
                    Y.append(Sphere(1))

            self._components[facet] = Y

    @staticmethod
    def __classcall_private__(cls, simplicial_complex):
        """
        TESTS::

            sage: MomentAngleComplex([[0,2], [1,2,3]]) is MomentAngleComplex([[0,2], [1,2,3]])
            True
            sage: Z = MomentAngleComplex([[0,2], [1,2,3]])
            sage: Z is MomentAngleComplex(Z)
            True
        """
        if simplicial_complex:
            if isinstance(simplicial_complex, MomentAngleComplex):
                # Allows for copy constructor
                immutable_complex = SimplicialComplex(simplicial_complex._simplicial_complex, is_mutable=False)
            elif not isinstance(simplicial_complex, SimplicialComplex):
                # Try to create a SimplicialComplex out of simplicial_complex
                # in case that simplicial_complex is a list of facets, or
                # something that can generate a SimplicialComplex
                immutable_complex = SimplicialComplex(simplicial_complex, is_mutable=False)
            elif simplicial_complex.is_mutable():
                immutable_complex = SimplicialComplex(simplicial_complex, is_mutable=False)
            else:
                immutable_complex = simplicial_complex
        else:
            immutable_complex = SimplicialComplex(is_mutable=False)
        return super().__classcall__(cls, immutable_complex)
        #behaviour for MomentAngleComplex()? maybe allow for simplexes?

    def _repr_(self):
        """
        Print representation.

        EXAMPLES::

        <Lots and lots of examples>
        """
        return "Moment-angle complex over a " + self._simplicial_complex._repr_().lower()

    @cached_method
    def create_complex(self):
        """
        Create the moment-angle complex as a simplicial complex.

        If this method is called, we also explicitly compute the
        moment-angle complex, viewed as a cubical complex, with the construction
        described above.

        .. WARNING::

            The construction can be very slow, it is not reccomended unless
            the corresponding simplicial complex has 5 or less vertices.

        EXAMPLES::

        <Lots and lots of examples>
        """
        n = len(self._simplicial_complex.vertices())
        D = [cubical_complexes.Cube(2)] * n
        S = [cubical_complexes.Sphere(1)] * n

        self._moment_angle_complex = CubicalComplex()
        for component in self._components.values():
            x = D[0] if component[0] == Simplex(2) else S[0]
            for j in range(1, len(component)):
                y = D[j] if component[j] == Simplex(2) else S[j]
                x = x.product(y)

            self._moment_angle_complex = union(self._moment_angle_complex, x)

    def components(self):
        """
        Return the dictionary of components of ``self``, indexed by facets
        of the simplicial complex.

        The values are lists, representing spheres and disks described in the
        construction of the moment-angle complex.

        EXAMPLES::

        <Lots and lots of examples>
        """

        return self._components

    #def homology(self, dim=None, base_ring=ZZ, subcomplex=None,
                 #generators=False, cohomology=False, algorithm='pari',
                 #verbose=False, reduced=True, **kwds):
        #"""
        #The (reduced) homology of this moment-angle complex.
#
#
        #.. SEEALSO::
            #:meth:`~sage.topology.cell_complex.homology`
#
        #EXAMPLES::
#
        #<Lots and lots of examples>
        #"""
        #if self._moment_angle_complex is None:
            #raise ValueError("the moment-angle complex is not created")
#
        #return self._moment_angle_complex.homology(dim, base_ring, subcomplex,
                 #generators, cohomology, algorithm,
                 #verbose, reduced, **kwds)

    def dimension(self):
        r"""
        The dimension of this moment-angle complex.

        The dimension of a moment-angle complex is the dimension
        of the constructed (cubical) complex. It is not difficult to
        see that this turns out to be `m+n+1`, where `m` is the number
        of vertices and `n` is the dimension of the associated simplicial
        complex.

        EXAMPLES::

        <Lots and lots of examples>
        """
        number_of_vertices = len(self._simplicial_complex.vertices())
        dim = self._simplicial_complex.dimension()
        return number_of_vertices + dim + 1

    def trivial_massey_product(self):
        """
        Return whether ``self`` has a non-trivial Massey product.

        This is the Massey product in the cohomology of the
        moment-angle complex.

        EXAMPLES::

        <Lots and lots of examples>
        """
        from sage.graphs.graph import Graph

        one_skeleton = self._simplicial_complex.graph()

        obstruction_graphs = [
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6), (2, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (4, 5), (1, 6), (2, 6), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (1, 6), (4, 5)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (1, 6), (4, 5), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (4, 5), (4, 6)]),
            Graph([(1, 2), (1, 4), (2, 3), (3, 5), (5, 6), (3, 4), (2, 6), (4, 6)]),
        ]

        return not any(one_skeleton.subgraph_search(g) is not None for g in obstruction_graphs)

    #needs work
    def golod_decomposition(self):
        """
        Determine whether ``self`` can be written (is homeomorphic) to a
        connected sum of sphere products, with two spheres in each product.

        This is done by checking the dimension and minimal non-Golodness of
        the associated simplicial complex.

        EXAMPLES::

        <Lots and lots of examples>
        """
        if self._simplicial_complex.dimension() % 2 != 0 or not self._simplicial_complex.is_minimally_non_golod():
            return False
            # or maybe NotImplementedError?

        B = self._simplicial_complex.bigraded_betti_numbers()
        x = {(B.get((a, b)), a+b) for (a, b) in B}
        D = {a : [] for (a, b) in x}
        for (a, b) in x:
            D[a].append(b)

        D.pop(1)

        out = ""
        for num in D:
            c1 = "S^" + str(D[num][0])
            if len(D[num]) == 1:
                c2 = " x " + c1
            for i in range(1, len(D[num])):
                c2 = " x S^" + str(D[num][i])

            out = out + " #(" + c1 + c2 + ")^" + str(num)
        # needs work
        return out

    @cached_method
    def _homology_group(self, l, base_ring=ZZ, cohomology=False,
                     algorithm='pari', verbose=False, reduced=True):
        """
        Expand the docstirng here.

        EXAMPLES::

        <Lots and lots of examples>
        """
        vertices = self._simplicial_complex.vertices()
        n = len(vertices)
        invfac = []

        for j in range(n+1):
            for x in combinations(vertices, j):
                S = self._simplicial_complex.generated_subcomplex(x)
                if base_ring.is_field():
                    invfac.append(S.homology(l-j-1, base_ring=base_ring,
                                             cohomology=cohomology, algorithm=algorithm,
                                             verbose=verbose, reduced=reduced).dimension())
                else:
                    invfac.extend(S.homology(l-j-1, base_ring=base_ring,
                                             cohomology=cohomology, algorithm=algorithm,
                                             verbose=verbose, reduced=reduced)._original_invts)

        m = len(invfac)
        if base_ring.is_field():
            return HomologyGroup(sum(invfac), base_ring)

        return HomologyGroup(m, base_ring, invfac)

    # expand the docstring here
    # should direct sum be implemented differently here?
    def homology(self, dim=None, base_ring=ZZ, cohomology=False,
                 algorithm='pari', verbose=False, reduced=True):
        """
        The reduced homology groups of ``self``, computed
        using Hochter's formula.

        EXAMPLES::

        <Lots and lots of examples>
        """
        if dim is not None:
            if isinstance(dim, (list, tuple, range)):
                low = min(dim)
                high = max(dim)
            else:
                low = dim
                high = dim
            dims = range(low, high + 1)
        else:
            dims = range(self.dimension()+1)

        answer = {i : self._homology_group(i, base_ring=base_ring,
                                             cohomology=cohomology, algorithm=algorithm,
                                             verbose=verbose, reduced=reduced) for i in dims}
        return answer

    def cohomology(self, dim=None, base_ring=ZZ, algorithm='pari',
                 verbose=False, reduced=True):
        r"""
        The reduced cohomology of this moment-angle complex.

        EXAMPLES::

        <Lots and lots of examples>
        """
        return self.homology(dim=dim, cohomology=True, base_ring=base_ring,
                             algorithm=algorithm, verbose=verbose, reduced=reduced)

    def betti(self, dim=None):
        r"""
        The Betti numbers of this moment-angle complex as a dictionary
        (or a single Betti number, if only one dimension is given):
        the ith Betti number is the rank of the ith homology group.

        :param dim: If ``None``, then return every Betti number, as
           a dictionary with keys the non-negative integers.  If
           ``dim`` is an integer or list, return the Betti number for
           each given dimension.  (Actually, if ``dim`` is a list,
           return the Betti numbers, as a dictionary, in the range
           from ``min(dim)`` to ``max(dim)``.  If ``dim`` is a number,
           return the Betti number in that dimension.)
        :type dim: integer or list of integers or ``None``; optional,
           default ``None``

        EXAMPLES:

        <Lots and lots of examples>
        """
        dict = {}
        H = self.homology(dim=dim, base_ring=QQ)
        try:
            for n in H.keys():
                dict[n] = H[n].dimension()
                if n == 0:
                    dict[n] += 1
            return dict
        except AttributeError:
            return H.dimension()

    def euler_characteristic(self):
        """
        Return the Euler characteristic of ``self``.

        EXAMPLES::

        <Lots and lots of examples>
        """
        return sum([(-1)**n * self.betti()[n] for n in range(self.dimension() + 1)])

    def product(self, other):
        """
        The product of this moment-angle complex with another one.

        It is known that the product of two moment-angle complexes
        is a moment-angle complex over the join of the two corresponding
        simplicial complexes.

        EXAMPLES:

        <Lots and lots of examples>
        """
        simplicial_complex = self._simplicial_complex.join(other._simplicial_complex, rename_vertices=True)
        return MomentAngleComplex(simplicial_complex)
