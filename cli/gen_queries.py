#!/usr/bin/env python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from oie_search.pipelines.generate_queries import main

if __name__ == "__main__":
    main()

