(in-package :mu-cl-resources)

;;; Workflow Builder

(define-resource pipeline ()
  :class (s-prefix "pwo:Workflow")
  :resource-base (s-url "http://www.big-data-europe.eu/data/workflows/")
  :properties `((:title :string ,(s-prefix "dcterms:title"))
                (:description :string ,(s-prefix "dcterms:description")))
  :has-one `((docker-compose :via ,(s-prefix "pwo:dockerComposeFile")
                              :as "docker-file"))
  :has-many `((step :via ,(s-prefix "pwo:hasStep")
                    :as "steps"))
  :on-path "pipelines")

(define-resource step ()
  :class (s-prefix "pwo:Step")
  :resource-base (s-url "http://www.big-data-europe.eu/data/steps/")
  :properties `((:title :string ,(s-prefix "dcterms:title"))
                (:description :string ,(s-prefix "dcterms:description"))
		(:code :string ,(s-prefix "pip:code"))
                (:order :number ,(s-prefix "pip:order"))
                (:status :string ,(s-prefix "pip:status")))
  :has-one `((pipeline :via ,(s-prefix "pwo:hasStep")
                       :inverse t
                       :as "pipeline"))
  :on-path "steps")

;;; Stack Builder

(define-resource docker-compose ()
  :class (s-prefix "stackbuilder:DockerCompose")
  :properties `((:text :string ,(s-prefix "stackbuilder:text"))
                (:title :string ,(s-prefix "dct:title")))
  :has-one `((pipeline :via ,(s-prefix "pwo:dockerComposeFile")
                              :inverse t
                              :as "related-workflows")
                              )
  :has-many `((stack :via ,(s-prefix "swarmui:dockerComposeFile")
                              :inverse t
                              :as "related-stacks")
              
                              )
  :resource-base (s-url "http://stack-builder.big-data-europe.eu/resources/docker-composes/")
  :on-path "docker-composes")


(define-resource container-item ()
  :class (s-prefix "stackbuilder:ContainerItem")
  :properties `((:title :string ,(s-prefix "dct:title"))
                (:repository :string ,(s-prefix "stackbuilder:repository"))
                (:docker-text :string ,(s-prefix "stackbuilder:dockerText")))
  :has-many `((container-relation :via ,(s-prefix "stackbuilder:relatedContainer")
                                :inverse t
                                :as "relations"))
  :resource-base (s-url "http://stack-builder.big-data-europe.eu/resources/container-items/")
  :on-path "container-items")

(define-resource container-group ()
  :class (s-prefix "stackbuilder:ContainerGroup")
  :properties `((:title :string ,(s-prefix "dct:title")))
  :has-many `((container-relation :via ,(s-prefix "stackbuilder:relatedGroup")
                                :inverse t
                                :as "relations"))
  :resource-base (s-url "http://stack-builder.big-data-europe.eu/resources/container-groups/")
  :on-path "container-groups")

(define-resource container-relation ()
  :class (s-prefix "stackbuilder:ContainerRelation")
  :properties `((:index :string ,(s-prefix "stackbuilder:index")))
  :has-one `((container-group :via ,(s-prefix "stackbuilder:relatedGroup")
                                :as "group")
              (container-item :via ,(s-prefix "stackbuilder:relatedContainer")
                                            :as "item"))
  :resource-base (s-url "http://stack-builder.big-data-europe.eu/resources/container-relations/")
  :on-path "container-relations")



;;; Swarm UI

(define-resource pipeline-instance ()
  :class (s-prefix "swarmui:Pipeline")
  :properties `((:title :string ,(s-prefix "dct:title"))
                (:icon :string ,(s-prefix "w3vocab:icon"))
                (:restart-requested :string ,(s-prefix "swarmui:restartRequested"))
                (:update-requested :string ,(s-prefix "swarmui:updateRequested")))
  :has-one `((stack :via ,(s-prefix "swarmui:pipelines")
                                    :inverse t
                                    :as "stack")
             (status :via ,(s-prefix "swarmui:status")
                     :as "status")
             (status :via ,(s-prefix "swarmui:requestedStatus")
                     :as "requested-status"))
  :has-many `((service :via ,(s-prefix "swarmui:services")
                       :as "services"))
  :resource-base (s-url "http://swarm-ui.big-data-europe.eu/resources/pipeline-instances/")
  :on-path "pipeline-instances")

(define-resource service ()
  :class (s-prefix "swarmui:Service")
  :properties `((:name :string ,(s-prefix "dct:title"))
                (:scaling :number ,(s-prefix "swarmui:scaling"))
                (:requested-scaling :number ,(s-prefix "swarmui:requestedScaling"))
                (:restart-requested :string ,(s-prefix "swarmui:restartRequested")))
  :has-one `((pipeline-instance :via ,(s-prefix "swarmui:services")
                                :inverse t
                                :as "pipeline-instance")
             (status :via ,(s-prefix "swarmui:status")
                     :as "status")
             (status :via ,(s-prefix "swarmui:requestedStatus")
                     :as "requested-status"))
  :resource-base (s-url "http://swarm-ui.big-data-europe.eu/resources/services/")
  :on-path "services")

(define-resource stack ()
  :class (s-prefix "doap:Stack")
  :properties `((:title :string ,(s-prefix "dct:title"))
                (:location :string ,(s-prefix "doap:location"))
                (:icon :string ,(s-prefix "w3vocab:icon")))
  :has-many `((pipeline-instance :via ,(s-prefix "swarmui:pipelines")
                                 :as "pipeline-instances"))
  :has-one `((docker-compose :via ,(s-prefix "swarmui:dockerComposeFile")
                                :as "docker-file"))
  :resource-base (s-url "http://swarm-ui.big-data-europe.eu/resources/stacks/")
  :on-path "stacks")

(define-resource status ()
  :class (s-prefix "swarmui:Status")
  :properties `((:title :string ,(s-prefix "dct:title")))
  :has-many `((pipeline-instance :via ,(s-prefix "swarmui:status")
                                 :inverse t
                                 :as "pipeline-instances"))
  :resource-base (s-url "http://swarm-ui.big-data-europe.eu/resources/statuses/")
  :on-path "statuses")
