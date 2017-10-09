(in-package :mu-cl-resources)

;;;;
;; NOTE
;; docker-compose stop; docker-compose rm; docker-compose up
;; after altering this file.


;;;;
;; Describe the prefixes which you'll use in the domain file here.
;; This is a short-form which allows you to write, for example,
;; (s-url "http://purl.org/dc/terms/title")
;; as (s-prefix "dct:title")

;; (add-prefix "dct" "http://purl.org/dc/terms/")


;;;;;
;; The following is the commented out version of those used in the
;; commented out domain.lisp.

;; (add-prefix "dcat" "http://www.w3.org/ns/dcat#")
;; (add-prefix "dct" "http://purl.org/dc/terms/")
;; (add-prefix "skos" "http://www.w3.org/2004/02/skos/core#")


;;;;;
;; You can use the muext: prefix when you're still searching for
;; the right predicates during development.  This should *not* be
;; used to publish any data under.  It's merely a prefix of which
;; the mu.semte.ch organisation indicates that it will not be used
;; by them and that it shouldn't be used for permanent URIs.

(add-prefix "ext" "http://mu.semte.ch/vocabularies/ext/")
(add-prefix "doap" "http://usefulinc.com/ns/doap#")
(add-prefix "w3vocab" "https://www.w3.org/1999/xhtml/vocab#")


(add-prefix "auth" "http://mu.semte.ch/vocabularies/authorization/")
(add-prefix "foaf" "http://xmlns.com/foaf/0.1/")
(add-prefix "mu" "http://mu.semte.ch/vocabularies/core/")
(add-prefix "dct" "http://purl.org/dc/terms/")
(add-prefix "stackbuilder" "http://stackbuilder.semte.ch/vocabularies/core/")
(add-prefix "swarmui" "http://swarmui.semte.ch/vocabularies/core/")


(add-prefix "dcterms" "http://purl.org/dc/terms/")
(add-prefix "pwo" "http://purl.org/spar/pwo/")
(add-prefix "pip" "http://www.big-data-europe.eu/vocabularies/pipeline/")
