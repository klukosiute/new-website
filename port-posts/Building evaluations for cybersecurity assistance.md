---
cover: files/cybsersec_card.png
og:image: files/cybsersec_card.png
description: On cybersecurity evaluations
---

# (Work in Progress) Building evaluations for cybersecurity assistance
Lately, I've been thinking about how language model evaluations should be built in order to reliably answer the questions a researcher is asking^[As opposed to: giving a proxy answer to a proxy question without much clarity on how applicable the result is. ].  I've come to ~zero conclusions on that so far, but as part of that thinking process, my colleague (an actual security expert) [Adam Swanda](https://deadbits.ai/)^[We did this work while we were still at Robust Intelligence, which was recently acquired by Cisco.] and I wrote a nifty little cybersecurity assistance usefulness evaluation. 

We recently presented this eval at [CAMLIS](https://www.camlis.org/) and made it [public](https://github.com/kamilelukosiute/yet-another-cybersec-assistance-eval), and so although I'm nowhere close to understanding how to build better evaluations, I thought I should briefly write about the thought process so far. It's all a work in progress: the eval is tiny, the thinking is fuzzy. Nevertheless, if I don't write about it now, I might never do it at all. 

What I'm calling "Yet Another Cybersecurity Assistance Evaluation" was inspired by how unsatisfying public language model evaluations for cybersecurity tasks feel to me. They just don't seem to be capable of answering the questions that I have. There are two reasons I can think of why this might be the case.

First, perhaps existing evaluations aren't simulating the threat model they are concerned with sufficiently accurately that I would trust conclusions drawn from the result. There are examples already where one set of researchers draws some conclusions about the *in*ability of a model to do something and then another set of researchers scaffolds the model that [fully saturates the benchmark](https://googleprojectzero.blogspot.com/2024/06/project-naptime.html). It seems unwise to trust the drawn conclusions if you don't trust the simulation. 

Second, perhaps I'm dissatisfied with the evaluations out there because I am not convinced that the threat models we are testing are the ones we should care about. For example, in 2022, you might've been extremely concerned about model-generated phishing text enabling actors to run way more attacks. Yet in 2024, nearly 2 years after the release of GPT-4... it just doesn't seem like the volume of phishing has gone up drastically? The [few reliable sources I can find](https://www.ic3.gov/AnnualReport/Reports/2023_IC3Report.pdf)^[See page 8.] of statistics on this find no increase in that time period. If automating phishing is such a big threat, then why is no one doing it? It's probably because it's not as big of a threat as we think. Adam tells me that, although writing phishing emails is *easy* for LLMs, it's just not the bottleneck for attackers. Instead, we should be concerned when LLMs start automating tasks that *are* bottlenecks for attackers. This requires modeling the adversary accurately, which is, of course, hard.

In building our cybersecurity assistance eval, Adam and I tried to address the first problem for one specific threat model: adversaries using LLMs as copilots throughout their attack development process. We aimed to build an a realistic cybersecurity assistance evaluation, based on our own experiences of talking to LLMs all day. We wrote prompts that are similarly phrased to how we seek assistance from LLMs on coding and research tasks. We're just two people, so of course it's likely not representative *in full*, but I like to think we did a decent job. Our prompts seem to be similar to the behaviours that OpenAI [report](https://cdn.openai.com/threat-intelligence-reports/influence-and-cyber-operations-an-update_October-2024.pdf) of threat actors (like asking for help debugging a script, or how to access user passwords in MacOS). 

So, that eval is now out there, and I still hope to figure out how to build better evals. The questions from this work in particular that remain are:
1. What are the threat models re: cybersecurity that actually matter right now, that incorporate both knowledge of model abilities *and* likelihood to empower adversaries?
2. To get a real understanding of the threat of LLMs in cybersecurity, do we need to have evals for every threat model or is there a way to model such abilities from a small set of evals?

That last question is really what I think about in the shower and on the train. [This paper](https://arxiv.org/abs/2405.10938) is the most exciting thing I've read all year. I really hope that method or some derivative of it works. If anyone wants to collaborate on answering these questions, please do reach out :) 

### Some results on the eval
Some results on Claude 3.5 Sonnet (Oct 2024), GPT-4o, and Gemini Pro below. This is a strange eval because it's not clear to me if "smaller is better" or "bigger is better." Interpret with many many grains of salt!!! 

Credit to [Nicholas Carlini](https://nicholas.carlini.com/writing/2024/my-benchmark-for-large-language-models.html) for the results visualisation (and also the evaluation framework).
<iframe src="https://kamilelukosiute.github.io/yet-another-cybersec-assistance-eval/" width="100%" height=400></iframe>
