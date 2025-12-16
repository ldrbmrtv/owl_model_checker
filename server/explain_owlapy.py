from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass
from owlapy.static_funcs import stopJVM

class SyncReasonerJustifications(SyncReasoner):

    def create_justifications(self, owl_individuals: None,
                              owl_class_expression: None,
                              save: bool = False):
        """
        Generate multiple justifications for why the given individual(s) are inferred to be instances of the specified class.

        Args:
            owl_individuals (Set[OWLNamedIndividual]): Set of individuals to explain.
            owl_class_expression (OWLClassExpression): Class expression to justify.
            save (bool): If True, saves all justifications in a new ontology as axioms.

        Returns:
            List[Set[OWLAxiom]]: Each item is a justification (set of OWLAxioms).
        """
        if owl_individuals is None or owl_class_expression is None:
            raise ValueError("Both owl_individuals and owl_class_expression are required.")

        from com.clarkparsia.owlapi.explanation import (
            BlackBoxExplanation, HSTExplanationGenerator, SatisfiabilityConverter
        )
        from openllet.owlapi import PelletReasonerFactory

        j_class_expr = self.mapper.map_(owl_class_expression)
        j_ontology = self._owlapi_ontology
        j_reasoner = self._owlapi_reasoner
        j_data_factory = self._owlapi_manager.getOWLDataFactory()

        reasoner_factory = PelletReasonerFactory.getInstance()
        blackbox_exp = BlackBoxExplanation(j_ontology, reasoner_factory, j_reasoner)
        explanation_gen = HSTExplanationGenerator(blackbox_exp)
        converter = SatisfiabilityConverter(j_data_factory)

        justifications = {}

        for ind in owl_individuals:
            j_individual = self.mapper.map_(ind)
            class_assertion_axiom = j_data_factory.getOWLClassAssertionAxiom(j_class_expr, j_individual)
            unsat_class = converter.convert(class_assertion_axiom)

            j_explanations = explanation_gen.getExplanations(unsat_class)
            
            justification = []
            for j_expl in j_explanations:
                #py_axioms = {self.mapper.map_(ax) for ax in j_expl}
                py_axioms = []
                for ax in j_expl:
                    #print(ax)
                    #py_axiom = self.mapper.map_(ax)
                    py_axiom = str(ax)
                    py_axioms.append(py_axiom)
                py_axioms = list(set(py_axioms))
            justification.append(py_axioms)
        
        justifications[ind.iri.remainder] = justification

        stopJVM()
        
        return justifications


#onto_iri = "http://test#NotCompliant"
#onto_path = 'C:/Users/baimu/Work/KIML/Explain/test_v1.rdf'
#expl = get_explanation(onto_iri, onto_path)
#print(expl)
