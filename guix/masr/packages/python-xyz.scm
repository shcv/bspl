;;; Copyright © 2025 Samuel Christie <shcv@sdf.org>

(define-module (masr packages python-xyz)
  #:use-module ((guix licenses) #:prefix license:)
  #:use-module (gnu packages)
  #:use-module (gnu packages base)
  #:use-module (gnu packages compression)
  #:use-module (gnu packages check)
  #:use-module (gnu packages python-check)
  #:use-module (gnu packages python-build)
  #:use-module (gnu packages python-xyz)
  #:use-module (gnu packages libffi)
  #:use-module (gnu packages time)
  #:use-module (gnu packages web)
  #:use-module (guix packages)
  #:use-module (guix download)
  #:use-module (guix build-system python)
  #:use-module (guix build-system pyproject)
  #:use-module (srfi srfi-1))

(define-public python-tatsu
  (package
    (name "python-tatsu")
    (version "5.12.1")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "TatSu" version ".zip"))
       (sha256
        (base32
         "1fz77p2ggn74bcj6lfn8q88z2snhia75mnawbv02hy1vyg6wn7jp"))))
    (build-system python-build-system)
    (arguments
     `(#:tests? #f))
    (native-inputs `(("unzip" ,unzip)
                     ("python-pytest-runner" ,python-pytest-runner)
                     ("python-pytest-mypy" ,python-pytest-mypy)))
    (home-page "https://github.com/neogeny/tatsu")
    (synopsis
     "TatSu takes a grammar in a variation of EBNF as input, and outputs a memoizing PEG/Packrat parser in Python.")
    (description
     "TatSu takes a grammar in a variation of EBNF as input, and outputs a memoizing PEG/Packrat parser in Python.")
    (license license:bsd-3)))

(define-public python-pytest-mypy
  (package
    (name "python-pytest-mypy")
    (version "1.0.1")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "pytest-mypy" version))
       (sha256
        (base32
         "077hmajyngi1rbxmq2nra6i1ckc000y74ndn82n9imd7zsj1im33"))))
    (build-system python-build-system)
    (propagated-inputs
     `(("python-attrs" ,python-attrs)
       ("python-filelock" ,python-filelock)
       ("python-mypy" ,python-mypy)
       ("python-pytest" ,python-pytest)))
    (native-inputs
     `(("python-setuptools-scm" ,python-setuptools-scm)))
    (home-page
     "https://github.com/dbader/pytest-mypy")
    (synopsis
     "Mypy static type checker plugin for Pytest")
    (description
     "Mypy static type checker plugin for Pytest")
    (license license:expat)))

(define-public python-setuptools-scm
  (package
    (name "python-setuptools-scm")
    (version "8.3.1")
    (source (origin
              (method url-fetch)
              (uri (pypi-uri "setuptools_scm" version))
              (sha256
               (base32
                "0ahlrxxkx2xhmxskx57gc96w3bdndflxx30304ihvm7ds136nny8"))))
    (build-system python-build-system)
    (home-page "https://github.com/pypa/setuptools_scm/")
    (synopsis "Manage Python package versions in SCM metadata")
    (description
     "Setuptools_scm handles managing your Python package versions in
@dfn{software configuration management} (SCM) metadata instead of declaring
them as the version argument or in a SCM managed file.")
    (license license:expat)))

(define-public python-boolexpr
  (package
    (name "python-boolexpr")
    (version "2.4")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "boolexpr" version))
       (sha256
        (base32
         "0bwzq1cp7lwnsh5n5paq6rgwagf6md2rlxr2m1lfa79r2rzp6jhp"))))
    (build-system python-build-system)
    (inputs
     (list glibc))
    (propagated-inputs
     (list python-cffi))
    (home-page "http://www.boolexpr.org")
    (synopsis "Boolean Expressions")
    (description "Boolean Expressions")
    (license license:asl2.0)))

(define-public python-ttictoc
  (package
    (name "python-ttictoc")
    (version "0.5.6")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "ttictoc" version))
       (sha256
        (base32
         "1nb436zyidwrqzzfz0r55s9nk05jjy7kysbiglzv36gjz8sabq4s"))))
    (build-system python-build-system)
    (home-page
     "https://github.com/hector-sab/ttictoc")
    (synopsis "Time parts of your code easily.")
    (description "Time parts of your code easily.")
    (license license:expat)))

(define-public python-aiorun
  (package
    (name "python-aiorun")
    (version "2025.1.1")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "aiorun" version))
       (sha256
        (base32
         "18sh1mym59s7rjwafv66s36q9rsg43lhdnrjnld6gqjc0dd0glc6"))))
    (build-system pyproject-build-system)
    (arguments
     '(#:phases
       (modify-phases %standard-phases
         (replace 'check
           (lambda* (#:key tests? #:allow-other-keys)
             (when tests?
               ;; Skip the test_sigterm_mp test entirely
               (invoke "python" "-m" "pytest" "-vvs" "-k" "not test_sigterm_mp")))))))
    (inputs
     (list python-pytest python-pytest-cov))
    (native-inputs
     (list python-flit-core))
    (home-page "https://github.com/cjrh/aiorun")
    (synopsis "Boilerplate for asyncio applications")
    (description
     "Boilerplate for asyncio applications")
    (license license:asl2.0)))

(define-public python-aiocron
  (package
    (name "python-aiocron")
    (version "1.8")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "aiocron" version))
       (sha256
        (base32
         "00asanv10gcw86irrv80xl303j2knskynr2swq0pkszjz89nam28"))))
    (build-system python-build-system)
    (propagated-inputs (list python-croniter python-tzlocal))
    (native-inputs (list python-pytest python-coverage))
    (home-page "https://github.com/gawel/aiocron/")
    (synopsis "Crontabs for asyncio")
    (description "Crontabs for asyncio")
    (license license:expat)))

(define-public python-ijson
  (package
    (name "python-ijson")
    (version "3.1.4")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "ijson" version))
       (sha256
        (base32
         "1sp463ywj4jv5cp6hsv2qwiima30d09xsabxb2dyq5b17jp0640x"))))
    (build-system python-build-system)
    (arguments
     `(#:phases
       (modify-phases %standard-phases
         (add-after 'unpack 'remove-unused-backend
           (lambda _
             (substitute* "test/test_base.py"
               (("(.*?)for backend in (.*?)'yajl', (.*)$" all indent prefix end)
                ;; remove 'yajl' from list of backends
                (string-append indent "for backend in " prefix end)))
             (delete-file "ijson/backends/yajl.py")
             #t)))))
    (propagated-inputs
     `(("python-cffi" ,python-cffi)
       ("libyajl" ,libyajl)))
    (home-page "https://github.com/ICRAR/ijson")
    (synopsis
     "Iterative JSON parser with standard Python iterator interfaces")
    (description
     "Iterative JSON parser with standard Python iterator interfaces")
    (license license:bsd-3)))

(define-public python-agentspeak
  (package
    (name "python-agentspeak")
    (version "0.1.0")
    (source (origin
              (method url-fetch)
              (uri (pypi-uri "agentspeak" version))
              (sha256
               (base32
                "1lfv22mi4l9psx6g3in2gzx0qs0qc3wrnckgszdn4y0k1vd9hgwz"))))
    (build-system python-build-system)
    (arguments
     `(#:tests? #f))
    (propagated-inputs (list python-colorama))
    (home-page "https://github.com/niklasf/python-agentspeak")
    (synopsis "JASON-style AgentSpeak for Python.")
    (description "JASON-style AgentSpeak for Python.")
    (license license:gpl3)))
