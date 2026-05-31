# aml-analytics
[![Tests](https://github.com/Bhavesh0205/aml-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/Bhavesh0205/aml-analytics/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/aml-analytics.svg)](https://pypi.org/project/aml-analytics/)
[![Downloads](https://pepy.tech/badge/aml-analytics/month)](https://pepy.tech/project/aml-analytics)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Open-source Python toolkit for AML detection and financial crime analytics — transaction graph analysis, anomaly scoring, SAR pattern matching, and SQL helpers for BSA/FinCEN compliance.

Built by a financial crimes analytics practitioner for compliance teams and data professionals working in anti-money laundering programs at financial institutions.

---

## Why this exists

Smaller financial institutions often lack the analytics infrastructure to detect sophisticated money laundering patterns. This toolkit provides open, reusable building blocks — grounded in FATF typologies and FinCEN advisories — that any compliance or data team can use to strengthen their AML detection program.

---

## AML typologies covered

| Typology | Module | Reference |
|---|---|---|
| Structuring (smurfing) | `aml/patterns.py` | FinCEN Advisory FIN-2014-A005 |
| Layering | `aml/graph.py` | FATF Typologies Report 2006 |
| Rapid fund movement | `aml/velocity.py` | FATF Guidance on AML/CFT 2012 |
| Network-based laundering | `aml/graph.py` | FinCEN Advisory FIN-2022-A001 |
| Anomalous transaction behavior | `aml/anomaly.py` | FATF Risk-Based Approach 2014 |

---

## Modules

| Module | Description |
|---|---|
| `aml/synthetic.py` | Synthetic AML transaction generator with labeled scenarios |
| `aml/graph.py` | Transaction network analysis — structuring rings, layering chains, centrality scoring |
| `aml/velocity.py` | Rolling-window velocity checks for burst activity detection |
| `aml/patterns.py` | Rules engine implementing FATF and FinCEN typologies |
| `aml/anomaly.py` | Unsupervised anomaly scoring using Isolation Forest and LOF |
| `aml/sql/` | Oracle and PostgreSQL query templates for AML detection |

---

## Quick start

```python
from aml.synthetic import generate_transactions
from aml.graph import build_network, detect_structuring, detect_layering

# Generate synthetic transaction data
txns = generate_transactions(n=1000)

# Build a transaction network
G = build_network(txns)

# Detect structuring rings
rings = detect_structuring(G, threshold=9000)

# Detect layering chains
chains = detect_layering(G, min_hops=3)

print(f"Structuring alerts: {len(rings)}")
print(f"Layering alerts:    {len(chains)}")
```

---

## Installation

```bash
pip install aml-analytics
```

Or install from source:

```bash
git clone https://github.com/Bhavesh0205/aml-analytics.git
cd aml-analytics
pip install -e ".[dev]"
```

---

## Demo notebooks

| Notebook | Description |
|---|---|
| `notebooks/01_graph_analysis.ipynb` | Transaction network analysis and layering detection |
| `notebooks/02_anomaly_detection.ipynb` | Unsupervised anomaly scoring on transaction data |
| `notebooks/03_sar_patterns.ipynb` | FATF typology rules and SAR pattern matching |
| `notebooks/04_end_to_end_pipeline.ipynb` | Full AML detection pipeline from raw transactions to alerts |

---

## Who this is for

- **Compliance analysts** who want to explore analytics-driven AML detection
- **Data engineers** building transaction monitoring pipelines at financial institutions
- **Researchers** studying financial crime detection methodology
- **FinTech developers** building AML capabilities into financial products

---

## Disclaimer

This toolkit is built entirely on synthetic data and public regulatory guidance (FATF, FinCEN). It does not contain any proprietary data, internal model logic, or confidential information from any financial institution. It is intended for educational and research purposes and does not constitute legal or compliance advice.

---

## Citation

If you use this toolkit in your research or work, please cite it as:

```bibtex
@software{aml_analytics,
  author  = {Bhavesh Awalkar},
  title   = {aml-analytics: Open-source toolkit for AML detection and financial crime analytics},
  year    = {2024},
  url     = {https://github.com/Bhavesh0205/aml-analytics},
  license = {MIT}
}
```

---

## Contributing

Contributions are welcome — especially new typology rules, additional SQL patterns, or improvements to the anomaly scoring module. Please read `CONTRIBUTING.md` before submitting a pull request.

---

## License

MIT — see `LICENSE` for details.
