from fastapi import FastAPI
from fastapi.responses import FileResponse
from rdflib import Graph, Namespace, RDF
from rdflib.namespace import SKOS
import re


app = FastAPI()


# ---------------------------------------------------------
# LOAD ONTOLOGY
# ---------------------------------------------------------

graph = Graph()
graph.parse("ontology/math-education-ontology.owl")


MATH = Namespace(
    "https://w3id.org/math-education-ontology#"
)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def get_id(resource):
    """
    Extrage partea locală din URI.

    Exemplu:
    https://w3id.org/math-education-ontology#Lesson_1
    ->
    Lesson_1
    """
    return str(resource).split("#")[-1]


def get_ro_text(subject, property_uri):
    """
    Returnează prima valoare în limba română
    pentru proprietatea cerută.
    """

    for value in graph.objects(
        subject,
        property_uri
    ):
        if getattr(
            value,
            "language",
            None
        ) == "ro":

            return str(value)

    return None


def natural_sort_key(value):
    """
    Sortează:
    Lesson_1, Lesson_2, Lesson_10

    în loc de:
    Lesson_1, Lesson_10, Lesson_2
    """

    parts = re.split(
        r"(\d+)",
        value
    )

    return [
        int(part)
        if part.isdigit()
        else part.lower()
        for part in parts
    ]


# ---------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------

@app.get("/")
def home():
    return FileResponse(
        "static/index.html"
    )


# ---------------------------------------------------------
# STATUS
# ---------------------------------------------------------

@app.get("/api/status")
def status():
    return {
        "message":
            "Math Ontology App is running",

        "triples":
            len(graph)
    }
@app.get("/api/stats")
def ontology_statistics():

    def count_type(class_uri):
        return sum(
            1
            for _ in graph.subjects(
                RDF.type,
                class_uri
            )
        )

    def count_property(property_uri):
        return sum(
            1
            for _ in graph.triples(
                (
                    None,
                    property_uri,
                    None
                )
            )
        )

    lessons_count = count_type(
        MATH.Lesson
    )

    concepts_count = count_type(
        MATH.MathematicalConcept
    )

    specific_competencies_count = count_type(
        MATH.SpecificCompetency
    )

    general_competencies_count = count_type(
        MATH.GeneralCompetency
    )

    return {

        "triples":
            len(graph),

        "lessons":
            lessons_count,

        "concepts":
            concepts_count,

        "specific_competencies":
            specific_competencies_count,

        "general_competencies":
            general_competencies_count,

        "competencies_total":
            (
                specific_competencies_count
                +
                general_competencies_count
            ),

        "relations": {

            "containsConcept":
                count_property(
                    MATH.containsConcept
                ),

            "developsCompetency":
                count_property(
                    MATH.developsCompetency
                ),

            "requiresPriorConcept":
                count_property(
                    MATH.requiresPriorConcept
                ),

            "hasPrerequisite":
                count_property(
                    MATH.hasPrerequisite
                ),

            "skosBroader":
                count_property(
                    SKOS.broader
                ),

            "requiresConcept":
                count_property(
                    MATH.requiresConcept
                )
        }
    }

# ---------------------------------------------------------
# LESSON LIST
# ---------------------------------------------------------

@app.get("/lessons")
def get_lessons():

    lessons = []


    for lesson in graph.subjects(
        RDF.type,
        MATH.Lesson
    ):

        lesson_id = get_id(lesson)


        lessons.append({

            "id":
                lesson_id,

            "label":
                get_ro_text(
                    lesson,
                    SKOS.prefLabel
                )
                or lesson_id

        })


    lessons.sort(
        key=lambda item:
            natural_sort_key(
                item["id"]
            )
    )


    return lessons


# ---------------------------------------------------------
# LESSON DETAILS
# ---------------------------------------------------------

@app.get("/lessons/{lesson_id}")
def get_lesson_details(
    lesson_id: str
):

    lesson = MATH[lesson_id]

    # -------------------------
    # PRIOR CONCEPTS
    # -------------------------

    prior_concepts = []

    for concept in graph.objects(
        lesson,
        MATH.requiresPriorConcept
    ):
        concept_id = get_id(concept)

        prior_concepts.append({
            "id": concept_id,
            "label": get_ro_text(
                concept,
                SKOS.prefLabel
            ) or concept_id
        })

    prior_concepts.sort(
        key=lambda item:
            natural_sort_key(item["id"])
    )
    # -------------------------
    # CONCEPTS
    # -------------------------

    concepts = []


    for concept in graph.objects(
        lesson,
        MATH.containsConcept
    ):

        concept_id = get_id(concept)


        concepts.append({

            "id":
                concept_id,

            "label":
                get_ro_text(
                    concept,
                    SKOS.prefLabel
                )
                or concept_id

        })


    concepts.sort(
        key=lambda item:
            natural_sort_key(
                item["id"]
            )
    )


    # -------------------------
    # COMPETENCIES
    # -------------------------

    competencies = []


    for competency in graph.objects(
        lesson,
        MATH.developsCompetency
    ):

        competency_id = get_id(
            competency
        )


        competencies.append({

            "id":
                competency_id,

            "label":
                get_ro_text(
                    competency,
                    SKOS.prefLabel
                )
                or competency_id

        })


    competencies.sort(
        key=lambda item:
            natural_sort_key(
                item["id"]
            )
    )


    return {

        "id":
            lesson_id,

        "label":
            get_ro_text(
                lesson,
                SKOS.prefLabel
            )
            or lesson_id,

        "definition":
            get_ro_text(
                lesson,
                SKOS.definition
            ),

        "scope_note":
            get_ro_text(
                lesson,
                SKOS.scopeNote
            ),

        "concepts":
            concepts,

        "prior_concepts":
            prior_concepts,

        "competencies":
            competencies

    }
    # -------------------------
    # PRIOR CONCEPTS
    # -------------------------



# ---------------------------------------------------------
# LESSON CONCEPTS
# ---------------------------------------------------------

@app.get(
    "/lessons/{lesson_id}/concepts"
)
def get_lesson_concepts(
    lesson_id: str
):

    lesson = MATH[lesson_id]

    concepts = []


    for concept in graph.objects(
        lesson,
        MATH.containsConcept
    ):

        concept_id = get_id(concept)


        concepts.append({

            "id":
                concept_id,

            "label":
                get_ro_text(
                    concept,
                    SKOS.prefLabel
                )
                or concept_id,

            "definition":
                get_ro_text(
                    concept,
                    SKOS.definition
                )

        })


    concepts.sort(
        key=lambda item:
            natural_sort_key(
                item["id"]
            )
    )


    return concepts


# ---------------------------------------------------------
# CONCEPT DETAILS
# ---------------------------------------------------------

@app.get(
    "/concepts/{concept_id}"
)
def get_concept(
    concept_id: str
):

    concept = MATH[concept_id]


    # -------------------------
    # NARROWER CONCEPTS
    # -------------------------

    narrower = []


    for child in graph.subjects(
        SKOS.broader,
        concept
    ):

        child_id = get_id(child)


        narrower.append({

            "id":
                child_id,

            "label":
                get_ro_text(
                    child,
                    SKOS.prefLabel
                )
                or child_id

        })


    narrower.sort(
        key=lambda item:
            natural_sort_key(
                item["id"]
            )
    )


    # -------------------------
    # BROADER CONCEPTS
    # -------------------------

    broader = []


    for parent in graph.objects(
        concept,
        SKOS.broader
    ):

        parent_id = get_id(parent)


        broader.append({

            "id":
                parent_id,

            "label":
                get_ro_text(
                    parent,
                    SKOS.prefLabel
                )
                or parent_id

        })


    # -------------------------
    # PREREQUISITES
    # -------------------------

    prerequisites = []


    for prerequisite in graph.objects(
        concept,
        MATH.hasPrerequisite
    ):

        prerequisite_id = get_id(
            prerequisite
        )


        prerequisites.append({

            "id":
                prerequisite_id,

            "label":
                get_ro_text(
                    prerequisite,
                    SKOS.prefLabel
                )
                or prerequisite_id

        })


    return {

        "id":
            concept_id,

        "label":
            get_ro_text(
                concept,
                SKOS.prefLabel
            )
            or concept_id,

        "definition":
            get_ro_text(
                concept,
                SKOS.definition
            ),

        "broader":
            broader,

        "narrower":
            narrower,

        "prerequisites":
            prerequisites

    }



# ---------------------------------------------------------
# LESSON GRAPH
# ---------------------------------------------------------

@app.get(
    "/lessons/{lesson_id}/graph"
)
def get_lesson_graph(
    lesson_id: str
):

    lesson = MATH[lesson_id]


    nodes = {}
    edges = []


    # -----------------------------------------------------
    # ADD NODE
    # -----------------------------------------------------

    def add_node(
        resource,
        node_type
    ):

        resource_id = get_id(
            resource
        )


        if resource_id not in nodes:

            nodes[resource_id] = {

                "id":
                    resource_id,

                "label":
                    get_ro_text(
                        resource,
                        SKOS.prefLabel
                    )
                    or resource_id,

                "type":
                    node_type

            }


        return resource_id


    # -----------------------------------------------------
    # LESSON NODE
    # -----------------------------------------------------

    lesson_node_id = add_node(
        lesson,
        "lesson"
    )


    # -----------------------------------------------------
    # MAIN CONCEPTS
    # -----------------------------------------------------

    main_concepts = list(
        graph.objects(
            lesson,
            MATH.containsConcept
        )
    )


    all_concepts = set(
        main_concepts
    )


    for concept in main_concepts:

        concept_id = add_node(
            concept,
            "concept"
        )


        edges.append({

            "source":
                lesson_node_id,

            "target":
                concept_id,

            "label":
                "containsConcept"

        })


        # ---------------------------------------------
        # SUBCONCEPTS
        # ---------------------------------------------

        for child in graph.subjects(
            SKOS.broader,
            concept
        ):

            all_concepts.add(
                child
            )


            child_id = add_node(
                child,
                "subconcept"
            )


            edges.append({

                "source":
                    concept_id,

                "target":
                    child_id,

                "label":
                    "narrower"

            })


    # -----------------------------------------------------
    # PREREQUISITES
    # -----------------------------------------------------

    for concept in list(
        all_concepts
    ):

        concept_id = add_node(
            concept,
            nodes.get(
                get_id(concept),
                {}
            ).get(
                "type",
                "concept"
            )
        )


        for prerequisite in graph.objects(
            concept,
            MATH.hasPrerequisite
        ):

            prerequisite_id = get_id(
                prerequisite
            )


            if prerequisite_id in nodes:

                add_node(
                    prerequisite,
                    nodes[
                        prerequisite_id
                    ]["type"]
                )

            else:

                add_node(
                    prerequisite,
                    "prerequisite"
                )


            edges.append({

                "source":
                    concept_id,

                "target":
                    prerequisite_id,

                "label":
                    "hasPrerequisite"

            })

        # -----------------------------------------------------
    # PRIOR CONCEPTS REQUIRED BY LESSON
    # -----------------------------------------------------

    for prior_concept in graph.objects(
        lesson,
        MATH.requiresPriorConcept
    ):

        prior_id = get_id(
            prior_concept
        )

        if prior_id not in nodes:

            add_node(
                prior_concept,
                "priorConcept"
            )

        edges.append({
            "source":
                lesson_node_id,

            "target":
                prior_id,

            "label":
                "requiresPriorConcept"
        })
    # -----------------------------------------------------
    # COMPETENCIES
    # -----------------------------------------------------

    competencies = list(
        graph.objects(
            lesson,
            MATH.developsCompetency
        )
    )


    for competency in competencies:

        competency_id = add_node(
            competency,
            "competency"
        )


        # Lesson -> Competency

        edges.append({

            "source":
                lesson_node_id,

            "target":
                competency_id,

            "label":
                "developsCompetency"

        })


        # ---------------------------------------------
        # Competency -> required concepts
        # ---------------------------------------------

        for required_concept in graph.objects(
            competency,
            MATH.requiresConcept
        ):

            required_id = get_id(
                required_concept
            )


            if required_id not in nodes:

                add_node(
                    required_concept,
                    "requiredConcept"
                )


            edges.append({

                "source":
                    competency_id,

                "target":
                    required_id,

                "label":
                    "requiresConcept"

            })


    return {

        "nodes":
            list(
                nodes.values()
            ),

        "edges":
            edges

    }
@app.get("/api/queries/lesson-prior/{lesson_id}")
def query_lesson_prior_concepts(lesson_id: str):

    query = f"""
    PREFIX math: <https://w3id.org/math-education-ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?concept ?label
    WHERE {{
        math:{lesson_id}
            math:requiresPriorConcept
            ?concept .

        OPTIONAL {{
            ?concept
                skos:prefLabel
                ?label .

            FILTER(
                lang(?label) = "ro"
            )
        }}
    }}
    ORDER BY ?concept
    """

    results = graph.query(query)

    concepts = []

    for row in results:

        concept_id = get_id(
            row.concept
        )

        concepts.append({
            "id": concept_id,
            "label":
                str(row.label)
                if row.label
                else concept_id
        })

    return {
        "lesson": lesson_id,
        "question":
            "Ce concepte trebuie cunoscute înainte de această lecție?",
        "results": concepts
    }
@app.get("/api/queries/lesson-competencies/{lesson_id}")
def query_lesson_competencies(lesson_id: str):

    query = f"""
    PREFIX math: <https://w3id.org/math-education-ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?competency ?label
    WHERE {{
        math:{lesson_id}
            math:developsCompetency
            ?competency .

        OPTIONAL {{
            ?competency
                skos:prefLabel
                ?label .

            FILTER(
                lang(?label) = "ro"
            )
        }}
    }}
    ORDER BY ?competency
    """

    results = graph.query(query)

    competencies = []

    for row in results:

        competency_id = get_id(
            row.competency
        )

        competencies.append({
            "id": competency_id,
            "label":
                str(row.label)
                if row.label
                else competency_id
        })

    return {
        "lesson": lesson_id,
        "question":
            "Ce competențe dezvoltă această lecție?",
        "results": competencies
    }
@app.get("/api/queries/concept-prerequisites/{concept_id}")
def query_concept_prerequisites(concept_id: str):

    query = f"""
    PREFIX math: <https://w3id.org/math-education-ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?prerequisite ?label
    WHERE {{
        math:{concept_id}
            math:hasPrerequisite
            ?prerequisite .

        OPTIONAL {{
            ?prerequisite
                skos:prefLabel
                ?label .

            FILTER(
                lang(?label) = "ro"
            )
        }}
    }}
    ORDER BY ?prerequisite
    """

    results = graph.query(query)

    prerequisites = []

    for row in results:

        prerequisite_id = get_id(
            row.prerequisite
        )

        prerequisites.append({
            "id": prerequisite_id,
            "label":
                str(row.label)
                if row.label
                else prerequisite_id
        })

    return {
        "concept": concept_id,
        "question":
            "De ce concepte depinde acest concept?",
        "results": prerequisites
    }
@app.get("/api/queries/competency-lessons/{competency_id}")
def query_competency_lessons(competency_id: str):

    query = f"""
    PREFIX math: <https://w3id.org/math-education-ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?lesson ?label
    WHERE {{
        ?lesson
            math:developsCompetency
            math:{competency_id} .

        OPTIONAL {{
            ?lesson
                skos:prefLabel
                ?label .

            FILTER(
                lang(?label) = "ro"
            )
        }}
    }}
    ORDER BY ?lesson
    """

    results = graph.query(query)

    lessons = []

    for row in results:

        lesson_id = get_id(
            row.lesson
        )

        lessons.append({
            "id": lesson_id,
            "label":
                str(row.label)
                if row.label
                else lesson_id
        })

    return {
        "competency": competency_id,
        "question":
            "Ce lecții dezvoltă această competență?",
        "results": lessons
    }

@app.get("/api/queries/concept-subconcepts/{concept_id}")
def query_concept_subconcepts(concept_id: str):

    query = f"""
    PREFIX math: <https://w3id.org/math-education-ontology#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?subconcept ?label
    WHERE {{
        ?subconcept
            skos:broader
            math:{concept_id} .

        OPTIONAL {{
            ?subconcept
                skos:prefLabel
                ?label .

            FILTER(
                lang(?label) = "ro"
            )
        }}
    }}
    ORDER BY ?subconcept
    """

    results = graph.query(query)

    subconcepts = []

    for row in results:

        subconcept_id = get_id(
            row.subconcept
        )

        subconcepts.append({
            "id": subconcept_id,
            "label":
                str(row.label)
                if row.label
                else subconcept_id
        })

    return {
        "concept": concept_id,
        "question":
            "Ce subconcepte are acest concept?",
        "results": subconcepts
    }

@app.get("/concepts")
def get_all_concepts():

    concepts = []

    for concept in graph.subjects(
        RDF.type,
        MATH.MathematicalConcept
    ):

        concept_id = get_id(concept)

        concepts.append({
            "id": concept_id,
            "label":
                get_ro_text(
                    concept,
                    SKOS.prefLabel
                )
                or concept_id
        })

    concepts.sort(
        key=lambda item:
            natural_sort_key(item["id"])
    )

    return concepts


@app.get("/competencies")
def get_all_competencies():

    competencies = []

    for competency in graph.subjects(
        RDF.type,
        MATH.SpecificCompetency
    ):

        competency_id = get_id(
            competency
        )

        competencies.append({
            "id": competency_id,
            "label":
                get_ro_text(
                    competency,
                    SKOS.prefLabel
                )
                or competency_id
        })

    competencies.sort(
        key=lambda item:
            natural_sort_key(item["id"])
    )

    return competencies