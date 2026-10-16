# RESEARCH BRIEF & PROJECT SPECIFICATION
## Internal Hidden State Probing and Hallucination Attribution in Multi-Step LLM Agent Trajectories

**Author / Researcher:** Purnachandra Madhukar  
**Academic Context:** MSc Data Science (Berlin)  
**Research Focus:** Autonomous LLM Agent Architecture | Trajectory Reliability | Mechanistic Interpretability  
**Status:** ACTIVE RESEARCH & BUILD TOPIC  
**Date Logged:** 2026-10-10  

---

## 1. EXECUTIVE SUMMARY & RESEARCH MOTIVATION

Autonomous LLM agents fail catastrophically when an error in step $t$ cascades into subsequent reasoning steps $t+1 \dots t+k$. Current industry approaches to error detection rely on:
1. **Self-Correction Prompting ("Are you sure?"):** Fails due to model sycophancy, reinforcement of identical priors, and inability to overcome high-probability token predictions.
2. **External LLM Evaluators / LLM-as-a-Judge:** Introduces 2x to 3x token overhead, high latency (3-6 seconds per validation call), and evaluates only surface textual coherence rather than factual veracity.

**The Thesis:**  
An LLM's internal representation space contains detectable geometric and activation signals that distinguish factual grounding from hallucination before the token is sampled. By extracting intermediate hidden states during multi-step agent trajectories, we can achieve:
- Real-time hallucination detection with zero additional generation tokens.
- Exact **step attribution**: Pinpointing which specific action or observation $t^*$ corrupted the agent's state belief.
- Trajectory rollbacks: Terminating corrupted paths early and backtracking before wasting compute.

---

## 2. THE MATHEMATICAL & ARCHITECTURAL FOUNDATION

### 2.1 The Representation Hypothesis
Let an autoregressive transformer process an agent trajectory sequence $X = (x_1, \dots, x_N)$.  
At layer $l \in [1, L]$ and token position $t$, the residual stream activation is:
$$h_l^{(t)} \in \mathbb{R}^D$$

While output token probabilities $P(x_{t+1} \mid X_{\le t}) = \text{softmax}(W_U h_L^{(t)})$ are easily distorted by language modeling fluency priors, intermediate representations $h_l^{(t)}$ retain distinct separability along a "truthfulness direction" $v_{\text{truth}} \in \mathbb{R}^D$.

### 2.2 Layer Sensitivity & Information Localization
Empirical studies across open-weight architectures (LLaMA-3, Mistral, Qwen-2.5) reveal that factuality signals are not uniformly distributed:
- **Early Layers ($l \in [1, 0.25 L]$):** Dominated by token embeddings, syntactic structures, and local n-gram parsing. Probes here achieve near-random accuracy on factual truthfulness.
- **Middle Layers ($l \in [0.45 L, 0.70 L]$):** Information routing, knowledge retrieval from MLP parameter matrices, and factual consistency are strongly localized here. Probes trained on layers 14–22 in 32-layer models achieve peak AUROC (0.84 - 0.92).
- **Late Layers ($l \in [0.85 L, L]$):** Shift toward output vocabulary distribution, surface token formatting, and punctuation alignment, diluting the pure semantic factuality signal.

---

## 3. PROBING METHODOLOGIES FOR AGENT TRAJECTORIES

### 3.1 Linear Probing (Difference-in-Means / Logistic Probes)
Training a linear classifier on intermediate activations:
$$\hat{y} = \sigma(w^T h_{l^*}^{(t)} + b)$$
- Fast inference ($<0.1$ ms per token).
- Interpretable weights $w$.
- Risk: Can overfit to superficial prompt artifacts if not normalized across diverse trajectory templates.

### 3.2 Unsupervised Geometry & Covariance (EigenScore / Entropy)
Instead of supervised labels, inspect the geometry of internal hidden states:
$$\text{Cov}(H) = \frac{1}{K} \sum_{i=1}^K (h_i - \bar{h})(h_i - \bar{h})^T$$
- EigenScore measures the eigenvalue distribution decay. High entropy / scattered subspace variance correlates with uncertain reasoning and hallucinated facts without requiring ground-truth supervision.

### 3.3 Trajectory Step Attribution Formulation
In an autonomous agent trajectory $T = (s_0, a_0, o_0, s_1, a_1, o_1, \dots, s_K, a_K, o_K)$:
For each decision step $k$:
1. Hook intermediate layers during the forward pass of action generation $a_k$.
2. Compute step confidence vector $c_k = f_{\text{probe}}(h_{l^*}(a_k))$.
3. Detect step drift:
$$\Delta_k = c_{k-1} - c_k$$
If $\Delta_k > \tau_{\text{drift}}$, step $k$ is flagged as the root cause of hallucination cascade.

---

## 4. PRIMARY EVIDENCE & LITERATURE REGISTRY

1. **Azaria & Mitchell (2023):** *"The Internal State of an LLM Knows When It's Lying"*  
   - Established that a simple MLP trained on hidden layers predicts statement veracity with 80%+ accuracy, outperforming verbalized confidence.
2. **MIND Framework (2024/2025):** *"Unsupervised Real-Time Hallucination Detection via Internal States"*  
   - Proved that internal representations signal hallucination without human labels or secondary LLM queries.
3. **EigenScore / Semantic Uncertainty (2024/2025):**  
   - Demonstrated that covariance eigenvalues in embedding subspaces distinguish true knowledge from confabulation.
4. **Trajectory Drift in AgentGym & SWE-bench (2025/2026):**  
   - Documented that 68% of agent failures stem from uncorrected false assumptions made within the first 3 trajectory steps.

---

## 5. BLUEPRINT FOR PURNA'S UPCOMING MAJOR BUILD

### Component 1: `trajectory-probe` Hook Engine (PyTorch / vLLM / HuggingFace)
- Lightweight forward-hook module intercepting intermediate activations:
  ```python
  def make_activation_hook(layer_idx, buffer):
      def hook(module, input, output):
          # output is (batch, seq_len, hidden_dim)
          buffer[layer_idx] = output[:, -1, :].detach().cpu()
      return hook
  ```
- Negligible latency overhead (<2% compute penalty during inference).

### Component 2: Step-Wise Attribution Monitor
- Real-time streaming monitor tracking trajectory step truthfulness.
- Outputs step-by-step confidence trajectory chart (visualizable via clean dashboard).

### Component 3: Early-Exit & Rollback Controller
- When step confidence drops below threshold $\tau = 0.42$:
  - Interrupt trajectory generation immediately.
  - Roll back environment state to checkpoint $s_{k-1}$.
  - Inject targeted constraint or re-plan prompt without hallucinated premise.

### Target Publication & Demo Goals
- **Benchmark Target:** Trajectory attribution accuracy on SWE-bench Verified and WebArena failure cases.
- **Efficiency Metric:** Reduction in wasted inference tokens (targeting 40-55% token savings on doomed trajectories).
- **Deliverables:** Open-source Python library, technical paper, and interactive visual demonstrator.
