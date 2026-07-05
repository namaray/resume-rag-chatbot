# Projects

## Pangochain — Blockchain Security Framework

### Overview
Pangochain is an open-source blockchain framework designed to provide enhanced security features for decentralized applications. It implements novel cryptographic protocols that improve transaction verification speed while maintaining strong security guarantees.

### Technical Details
- **Language**: Python, with performance-critical components in Rust
- **Architecture**: Modular blockchain framework with pluggable consensus mechanisms
- **Key Innovation**: Custom hash-chain verification protocol that reduces block validation time by 40% compared to traditional approaches
- **Cryptography**: Implements SHA-256, ECDSA signing, and a custom Merkle tree variant optimized for high-throughput transaction verification

### Features
- Lightweight node implementation suitable for resource-constrained environments
- RESTful API for interacting with the blockchain network
- Built-in smart contract support with a sandboxed execution environment
- Comprehensive logging and audit trail for all network activities
- Dockerized deployment for easy setup and testing

### Key Achievements
- Successfully processed 1,000+ transactions per second in benchmark testing
- Implemented integrity verification through cryptographic hash chains
- Open-sourced with documentation and example applications
- Presented at university blockchain symposium

### Repository
Available on GitHub with full documentation, unit tests, and deployment guides.

---

## ML Research — Domain Adaptation with SegFormer and Mixture of Experts

### Overview
Research project investigating how Mixture of Experts (MoE) architectures can improve domain adaptation performance in semantic segmentation tasks. The work focuses on adapting SegFormer models trained on one visual domain to perform well on a different target domain without extensive retraining.

### Problem Statement
Semantic segmentation models often suffer significant performance drops when applied to domains different from their training data (e.g., a model trained on daytime driving scenes performing poorly on nighttime or rainy conditions). Traditional fine-tuning approaches require large amounts of labeled target domain data, which is expensive and time-consuming to obtain.

### Approach
- **Base Model**: SegFormer (hierarchical Transformer encoder with a lightweight MLP decoder)
- **MoE Integration**: Added Mixture of Experts layers that learn to route different input features to specialized expert networks based on domain characteristics
- **Training Strategy**: Two-phase training — first pre-train on source domain, then adapt using MoE routing with minimal target domain supervision
- **Evaluation**: Tested on Cityscapes → ACDC (adverse conditions) and GTA5 → Cityscapes benchmarks

### Results
- Achieved 12% improvement in mean Intersection over Union (mIoU) compared to vanilla SegFormer domain adaptation
- MoE routing learned interpretable specializations: some experts specialized in weather-related features, others in lighting conditions
- Reduced the need for target domain labeled data by 60% compared to full fine-tuning approaches

### Technologies Used
- PyTorch, Hugging Face Transformers, MMSegmentation
- NVIDIA A100 GPUs for training
- Weights & Biases for experiment tracking
- Python, NumPy, OpenCV for data preprocessing

### Publications
Research paper in preparation for submission to a computer vision conference.

---

## Portfolio Website

### Overview
Personal portfolio website showcasing projects, skills, and professional experience. Built with modern web technologies and featuring an interactive resume chatbot (this project).

### Technical Details
- **Frontend**: HTML, CSS, JavaScript with responsive design
- **Hosting**: Deployed on Vercel/Netlify
- **Features**: Project showcase, blog section, contact form, interactive resume chatbot widget
- **Design**: Dark theme with glassmorphism effects, smooth animations, and mobile-first approach

---

## AI Accessibility Tool — Hackathon Winner

### Overview
An AI-powered tool that automatically generates alt-text descriptions for images on websites, making web content more accessible for visually impaired users. Won 1st place at University Hackathon 2024.

### Technical Details
- Built in 36 hours during a hackathon
- Uses a fine-tuned vision-language model for image captioning
- Browser extension that scans web pages and fills in missing alt-text
- Backend API processing images and returning descriptive captions
- **Tech stack**: Python, FastAPI, Hugging Face models, JavaScript browser extension
