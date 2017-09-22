(in-package :mu-cl-resources)

;;; Stack Builder

(define-resource docker-compose ()
  :class (s-prefix "stackbuilder:DockerCompose")
  :properties `((:text :string ,(s-prefix "stackbuilder:text"))
                (:title :string ,(s-prefix "dct:title")))
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
