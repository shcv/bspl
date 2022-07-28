;;; Copyright © 2021 Samuel Christie <shcv@sdf.org>

(define-module (masr packages)
  #:use-module (masr packages python-xyz)
  #:use-module ((guix licenses) #:prefix license:)
  #:use-module (gnu packages)
  #:use-module (gnu packages base)
  #:use-module (gnu packages check)
  #:use-module (gnu packages python-xyz)
  #:use-module (gnu packages python-web)
  #:use-module (guix packages)
  #:use-module (guix gexp)
  #:use-module (guix git-download)
  #:use-module (guix build-system python)
  #:use-module (srfi srfi-1))

(define-public python-bspl
  (package
    (name "python-bspl")
    (version "0.0.0")
    (source
     (origin
       (method git-fetch)
       (uri (git-reference
             (url "https://gitlab.com/masr/bspl")
             (commit "f853c145e9c425eb99eddc5a9559737376eb5e2")))
       (sha256
        (base32
         "1ir949z28ng4xll3pd0n3clizd5n378qa634vc8kvkxna4cghn70"))))
    (build-system python-build-system)
    (propagated-inputs
     (list
      python-agentspeak
      python-aiocron
      python-aiorun
      python-boolexpr
      python-colorama
      python-fire
      python-ijson
      python-pyyaml
      python-simplejson
      python-tatsu
      python-ttictoc
      python-uvloop))
    (native-inputs
     (list python-setuptools-git
           python-pytest
           python-pytest-asyncio))
    (arguments
     `(#:phases
       (modify-phases %standard-phases
         (replace 'check
           (lambda _
             (setenv "PYTHONPATH" "src")
             (invoke "pytest"))))))
    (home-page "https://gitlab.com/masr/bspl")
    (synopsis "A python framework for implementing agents according to protocol specifications")
    (description "This repository provides tools for working with the language, including a parser and verification tools (proving safety, liveness, etc.))))
It also provides a library for implementing agents that can enact BSPL protocols.")
    (license license:expat)))

(define-public python-bspl-dev
  (package
    (inherit python-bspl)
    (name "python-bspl-dev")
    (source (local-file (getcwd) #:recursive? #t))))
