# What does BCEWithLogits actually do?
Binary classification will typically involve taking a sigmoid of your final neural network layer outputs and computing the binary cross entropy loss (BCE). Sigmoid has exponentials, and BCE has logarithms, so some clever people who write PyTorch decided that it would probably be wise to combine those two operations into one class, so now we have the function `BCEWithLogitsLoss`. This blog post aims to explain exactly what is being done by this function and why it is better to use this function rather than computing sigmoid and BCE separately. 

## BCE and Sigmoid in Binary Classification
The BCE loss is just the negative log likelihood of the Bernoulli distribution:

$$
\mathcal{L} = - \sum_{i=1}^N t_i \log y_i + (1-t_i) \log(1-y_i)
$$

Here, $t_i$ is the target value and $y_i$ is the prediction by the model. In the case of a neural network, $y_i$ is usually given by the sigmoid function applied on top of the final layer output to convert the outputs into probabilities. The sigmoid function is

$$
y_i=  \sigma(z_i )= \frac{1}{1+e^{-z_i}} = \frac{e^{z_i}}{e^{z_i}+1}
$$

where $z_i$ is any real number i.e. the output of the final neural network layer.

## BCEWithLogitsLoss
Now, of course you could implement these equations naively and do these two operations separately. PyTorch allows you to do that with the functions `torch.nn.BCELoss()` and `torch.nn.Sigmoid()`. However, notice that there's some exponentials in the sigmoid and a logarithm in the loss. Surely, some of those will cancel out if you put the expressions together, and you can save on precious precious FLOPS, right? Perhaps you gain some other benefits too, such as numerical stability, if you do so? 

Enter `BCEWithLogitsLoss()`, which combines the two operations into one and, [as per the documentation](https://pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html?highlight=bce%20loss%20logits#torch.nn.BCEWithLogitsLoss), takes "advantage of the log-sum-exp trick for numerical stability." I thought of log-sum-exp as something one does when they compute a numerically stable Softmax (read more about log-sum-exp [here](https://gregorygundersen.com/blog/2020/02/09/log-sum-exp/)), so I wasn't entirely sure how it applied in this situation. To better understand what PyTorch is actually doing, it is sometimes possible to find the exact C++ snippet that's called when you call the Python function. The C++ function that is called when you call `torch.nn.BCEWithLogitsLoss()` (which calls `torch.binary_cross_entropy_with_logits`) can be found [here](https://github.com/pytorch/pytorch/blob/35fed93b1ef05175143f883c6f89f06c6dd9429b/aten/src/ATen/native/Loss.cpp#L96-L112), but I've provided it below for convenience:
```cpp
Tensor binary_cross_entropy_with_logits(const Tensor& input, const Tensor& target, const Tensor& weight, const Tensor& pos_weight, int64_t reduction) {
	Tensor loss;
	auto max_val = (-input).clamp_min_(0);
	if (pos_weight.defined()) {
	// pos_weight need to be broadcasted, thus mul(target) is not inplace.
	auto log_weight = (pos_weight - 1).mul(target).add_(1);
	loss = (1 - target).mul_(input).add_(log_weight.mul_(((-max_val).exp_().add_((-input - max_val).exp_())).log_().add_(max_val)));
	} else {
	loss = (1 - target).mul_(input).add_(max_val).add_((-max_val).exp_().add_((-input -max_val).exp_()).log_());
	}
	
	if (weight.defined()) {
	loss.mul_(weight);
	}
	
	return apply_loss_reduction(loss, reduction);
}
```
First, this function computes a maximum value (`max_val`). Then, depending on whether or not you've provided positive weights (the documentation says: "It’s possible to trade off recall and precision by adding weights to positive examples."), two different operations are performed to compute loss per example. After that, you can apply weighting per element as well. Lastly, a loss reduction is performed (mean or sum).
## Deriving the BCEWithLogitsLoss C++ Expression
The key line from the snippet above for us is what happens after `else`:
```cpp
loss = (1 - target).mul_(input).add_(max_val).add_((-max_val).exp_().add_((-input -max_val).exp_()).log_());
```

For readability, let me translate this to an equation:

$$
\mathcal{L}_i = (1-t_i)(z_i) + C + \log (e^{-C} + e^{-z_i-C})
$$

Here, $t_i$ is the target, $z_i$ is the raw neural network output (in $\mathbb{R}$) and $C$ is the largest value in the batch.

Now, this doesn't look like any BCE loss I've ever seen before. Where did this come from? Let's do a quick derivation, where I am being extra explicit between each step, starting by taking apart the terms of the BCE loss:

$$
\begin{align}
\mathcal{L} &= - \sum_{i=1}^N t_i \log y_i +\log(1-y_i) -t_i\log(1-y_i) \\
 &= - \sum_{i=1}^N t_i \log \sigma(z_i) +\log(1-\sigma(z_i)) -t_i\log(1-\sigma(z_i)) \\
 &= - \sum_{i=1}^N t_i(\log \sigma(z_i) -\log\sigma(-z_i)) +\log\sigma(-z_i)  \\
 &= - \sum_{i=1}^N t_i \log \Big( \frac{\sigma(z_i)}{\sigma(-z_i)} \Big) +\log\sigma(-z_i) \\
 &= - \sum_{i=1}^N t_i \log e^{z_i} +\log\Big( \frac{e^{-z_i}}{1 + e^{-z_i}} \Big) \\
 &= - \sum_{i=1}^N t_i z_i +\log(e^{-z_i}) - \log(1 + e^{-z_i}) \\ 
 &= - \sum_{i=1}^N t_i z_i -z_i - \log(1 + e^{-z_i}) \\ 
 &=  \sum_{i=1}^N (1-t_i) z_i + \log(1 + e^{-z_i}) 
\end{align}
$$

Now that looks much closer to our C++! In the third line we take advantage of the sigmoid identity $\sigma (-x) = 1 - \sigma(x)$. In the remainder of the lines, we take advantage of various exponential and logarithmic identities. Now, we are only missing the maximum value, $C$.

## Numerical Stability of  $\log (1 + e^{-x})$
To understand where the maximum value enters the picture, consider what  $$1 + e^{-x}$$ looks like: 
![[exp_func.png| center | 400]]

The function blows up for large negative values. Indeed, PyTorch would be very unhappy if you tried to compute $1 + e^{-x}$  even for seemingly reasonable $x$'s:
```python
x = torch.Tensor([-100, 1,10,100])
print(1+torch.exp(-x))

tensor([ inf, 1.3679, 1.0000, 1.0000])
```


For large positive values of $x$, it simply puts out 0 for $e^{-x}$ and the entire thing becomes equal to 1 (no problem). But for large negative values, the output becomes infinite. However, we end up taking a _logarithm_ immediately after computing this expression, and that logarithm would make the value be non-infinite again. Yet if $e^{-x}$ returns infinity, we lose information. To avoid this, we want the exponent in $e^{-x}$ to not reach too large values. We can achieve this by shifting and then unshifting the entire computation.

We aim to shift the values of $x$ towards 0 and more positive values. If $x$ is a large negative value, we should add a large positive value to it (a reasonable choice is the maximum value) so that

$$
e^{-x} \rightarrow e^{-(x+C)} = e^{-x-C}
$$

So that's what we're looking to have in the exponent. To achieve this while maintaining the same final output, we need to do the following operation on our loss expression:

$$
\begin{align}
\mathcal{L} &= \sum_{i=1}^N (1-t_i) z_i + C - C + \log(1 + e^{-z_i}) \\
&=  \sum_{i=1}^N(1-t_i) z_i + C - C + \log(e^{-C}(1 + e^{-z_i}))\\
&=  \sum_{i=1}^N(1-t_i) z_i + C + \log(e^{-C} + e^{-z_i-C})
\end{align}
$$

I think the subtraction of the maximum value in the exponent and adding it back in to shift and unshift the computation is what the documentation means by "log-sum-exp trick." I actually don't think this is that trick, since I believe log-sum-exp refers to the  when you take a log such that you can get a stable exponential computation, in a place where a log was not naturally present. However, we had the log to start with from the BCE loss. The idea of adding the maximum value is closely related, and I would call it the [exp-normalize trick](https://timvieira.github.io/blog/post/2014/02/11/exp-normalize-trick/).

Regardless of what it's called, using `BCEWithLogitsLoss` instead of a sigmoid followed by BCE makes a lot of sense. First, because we can simplify the expression after we combine the exponentials from the sigmoid and the logarithms from the BCE, we simply have fewer computations. Second, the exp-normalize trick avoids the exploding outputs when $x$ is negative and large. With the normal strategy of doing the operations separately, you don't get these nice benefits.

*Originally Published on Apr 14, 2022*