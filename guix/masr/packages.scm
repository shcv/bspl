;;; Copyright © 2021 Samuel Christie <shcv@sdf.org>

(define-module (masr packages)
  #:use-module (masr packages python-xyz)
  #:use-module ((guix licenses) #:prefix license:)
  #:use-module (gnu packages)
  #:use-module (gnu packages check)
  #:use-module (gnu packages python-xyz)
  #:use-module (gnu packages python-web)
  #:use-module (guix packages)
  #:use-module (guix git-download)
  #:use-module (guix build-system python)
  #:use-module (srfi srfi-1))

(define-public protocheck
  (package
    (name "protocheck")
    (version "0.3.0")
    (source
     (origin
       (method git-fetch)
       (uri (git-reference
             (url "https://gitlab.com/masr/protocheck")
             (commit "61623fa6821db7ffc12cd5d2aaba591ae2fc526")))
       (sha256
        (base32
         "0x818sfcw49c6zfc42yrnin20q3fp5095aigmyzv3ybihs8qpsan"))))
    (build-system python-build-system)
    (propagated-inputs
     `(("python-ttictoc" ,python-ttictoc)
       ("python-simplejson" ,python-simplejson)
       ("python-configargparse" ,python-configargparse)
       ("python-boolexpr" ,python-boolexpr)
       ("python-tatsu" ,python-tatsu)))
    (native-inputs
     `(("python-setuptools-git" ,python-setuptools-git)
       ("python-pytest" ,python-pytest)))
    (home-page "https://gitlab.com/masr/protocheck")
    (synopsis "BSPL protocol tool suite")
    (description "Protocheck is a tool suite for parsing, verifying, and working with BSPL protocol specifications.")
    (license license:expat)))

(define-public python-bungie
  (package
    (name "python-bungie")
    (version "0.0.0")
    (source
     (origin
       (method git-fetch)
       (uri (git-reference
             (url "https://gitlab.com/masr/bungie")
             (commit "f853c145e9c425eb99eddc5a9559737376eb5e2")))
       (sha256
        (base32
         "1ir949z28ng4xll3pd0n3clizd5n378qa634vc8kvkxna4cghn70"))))
    (build-system python-build-system)
    (native-inputs
     `(("python-setuptools-git" ,python-setuptools-git)
       ("python-pytest" ,python-pytest)))
    (propagated-inputs
     `(("protocheck" ,protocheck)
       ("python-tatsu" ,python-tatsu)
       ("python-uvloop" ,python-uvloop)
       ("python-aiorun" ,python-aiorun)
       ("python-aiocron" ,python-aiocron)
       ("python-ijson" ,python-ijson)
       ("python-pyyaml" ,python-pyyaml)))
    (home-page "https://gitlab.com/masr/bungie")
    (synopsis "A python framework for implementing fault tolerant agents as microservices")
    (description "Bungie is a simple framework for implementing agents as microservices, with additional support for fault-tolerance policies.")
    (license license:expat)))

