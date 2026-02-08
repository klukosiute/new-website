# When can a tensor be view()ed?
A common operation in PyTorch is taking a tensor with the same data and giving it a new shape. The usual method to do this is to call `torch.Tensor.view(new_shape)`. This operation is nice because the returned tensor shares the underlying data with the original tensor, which avoids data copy and makes the reshaping memory-efficient. This of course introduces the usual quirk that if you change a value in the original tensor, the corresponding value will change in the `.view()`ed tensor. 

`.view()` cannot always be used. At minimum, `new_shape` must have the same total number of elements as the original tensor. There are also additional requirements for the compatibility of the old and new shapes. However, the documentation about this is kinda opaque, so the purpose of this blog post is to try to understand those requirements in more detail. 

(If you know PyTorch better than I do, and I got something wrong here, please contact me!)

Let's begin with what [the torch documentation](https://pytorch.org/docs/stable/generated/torch.Tensor.view.html#torch.Tensor.view) says:
>For a tensor to be viewed, the new view size must be compatible with its original size and stride, i.e., each new view dimension must either be a subspace of an original dimension, or only span across original dimensions $d, d+1, \dots, d+k$ that satisfy the following contiguity-like condition that $\forall i = d, \dots, d+k-1$,
> $$\text{stride}[i] = \text{stride}[i+1] \times \text{size}[i+1] $$

There are two conditions given here; notice that the tensor need only satisfy _one_ of them. The first is the "subspace" condition and the second is the "contiguity-like" condition. Let's start with the second condition, since when you create tensors in PyTorch, they are by default contiguous.
### Contiguity-like condition
Let's create a tensor to work with as an example:
```python
z = torch.arange(12).reshape(3,4)
print(z)

tensor([[ 0, 1, 2, 3],  
		[ 4, 5, 6, 7], 
		[ 8, 9, 10, 11]])
```

PyTorch tensors are stored by default in C row order so that our tensor `z` 
![[matrix.png | 200]]
is stored in memory like so:
![[matrix_memory.png]]
The "contiguity-like" condition involves thinking about how you would access adjacent elements in memory in order to provide the elements of the new array. 

Our example is a two dimensional tensor, meaning that the original dimensions are 0 and 1. We can see the size of these dimensions by just calling  `size()`:
```python
print(z.size())

torch.Size([3, 4])
```

Alright, so what's stride? `torch.Tensor.stride(dim)` is the "jump necessary to go from one element to the next one in the specified dimension `dim`" in computer memory. We can look at this value by calling `stride()`:
```python
print(z.stride())

(4,1)
```

What this is telling us is that, to access adjacent values in the 0th dimension (i.e. to access values that make up a column), we need to jump by 4 values in memory. To access adjacent values in the 1st dimension (i.e. to access values that make up a row), we only need to jump by 1 value. 

When you call `view()` on an array, the original memory storage is not changed, but the `stride()` _is_ changed, and therefore has to be compatible with the original stride. This is what the "contiguity-like" condition is telling us.

Let's say I want to reshape `z` into shape (6,2). To see if this is possible, I can check the condition specified in the documentation. First, we need to determine which dimensions our new dimensions will span across. The statement $\forall i = d, \dots, d+k-1$ is looking for all dimensions from dimension $d$ to $d+k-1$ where $k$ is the count of dimensions that the new dimensions span across _minus one_ (I don't know why it's like this, but it can't be anything else or it doesn't work out). So you need to check all the old dimensions that the new dimensions span across except the last one. Then, the condition to check is that $\forall i = d, \dots, d+k-1$,
$$
\text{stride}[i] = \text{stride}[i+1] \times \text{size}[i+1]
$$
Before actually doing the computation, let's think briefly about what this condition is saying. First, notice that the condition is on the _original_ dimensions that the new dimensions span across. PyTorch expects the original tensor to be row-contiguous in order to reshape it, and that's basically what the condition is checking: if I take a step in dimension $i$, which requires me to take the number of steps returned by $\text{stride}[i]$, do I step over an entire row of a later dimension $i+1$, which would require taking $\text{stride}[i+1] \times \text{size}[i+1]$ steps? This is equivalent to asking if dimension $i$ is row-contiguous.

Coming back to our example now, our new dimensions will span across _both_ of the old ones, so $d=0, k=2-1=1$ so we need to check just the original 0th dimension: $\text{stride}[0] = \text{stride}[1] \times \text{size}[1]$ $4 = 1 \times 4$. Great, since our original `z` is contiguous, we can use `view()` to turn it into any shape that has the same number of elements i.e. 12:

```python
print(z.view(6,2))

tensor([[ 0, 1],  
		[ 2, 3],  
		[ 4, 5],  
		[ 6, 7],  
		[ 8, 9],  
		[10, 11]])
```

I can also take a look at the new stride and see that, to jump along the 0th dimension, we need to now jump by 2 values
```python
print(z.view(6,2).stride())

(2, 1)
```
but the new viewed tensor is still contiguous. 

So when would the "contiguity-like" condition NOT hold? We can make a very similar tensor
```python
z_t = torch.arange(12).reshape(3,4).t()
print(z_t)

tensor([[ 0, 4, 8],  
		[ 1, 5, 9],  
		[ 2, 6, 10],  
		[ 3, 7, 11]])
```
but this tensor is no longer row-contiguous. In `torch`, a transposed tensor shares the same underlying data as the original, but that means that contiguity is lost because adjacent values are no longer contiguous in memory. It's now the _columns_ that are contiguous in memory i.e.
![[matrix_transpose.png|150]]
But in memory, it still looks like so:
![[matrix_memory.png]]

We can also see this by looking at the stride of `z_t`:
```python
print(z_t.stride())

(1,4)
```

Could we use `view()` to reshape `z_t` into shape 6,2? We check the contiguity-like condition:
$$
\text{stride}[0] = \text{stride}[1] \times \text{size}[1]
$$
$$
1 \not= 4 \times 3
$$
and we see that it does not hold. 
### Subspace condition
There _are_ other shapes we could give `z_t` with `.view()`, however. Imagine we would like to reshape it into shape 2,2,3. The contiguity-like condition does not hold because the original tensor is not contiguous, but now we can check the second condition ("each new view dimension must either be a subspace of an original dimension").

We can think of reshaping `(4,3) -> (2,2,3)` as splitting dimension 0 into two "subspaces." I actually can't quite figure out if this "subspace" has anything to do with a proper linear algebra subspace, but that's not the most important thing. I can definitely tell you that, even when a tensor is not contiguous, you can reshape it if you are only affecting one dimension at a time. For example, here, we are splitting the 0th dimension into two dimensions of size 2 each:
```python
print(z_t.view(2,2,3))

tensor([[[ 0, 4, 8],  
		 [ 1, 5, 9]],  
		
		[[ 2, 6, 10],  
		 [ 3, 7, 11]]])
```

We can also look at the stride of _this_ tensor
```python
print(z_t.view(2,2,3).stride())

(2,1,4)
```
and see that the first two dimensions are contiguous while the last one is not. (As far as I can tell, your tensor is contiguous if the values of the stride are in descending order.)

So these are the two conditions when you can `view()` a tensor: when you can reshape it simply by reassigning new values of the stride, or when you can split each dimension individually, and our question is answered. Below, I have some additional notes that may be of use. 

### Addendum
When you can't use `.view()` to reshape your tensor, you can call `.contiguous()`, which makes a copy of the tensor in a new chunk of memory such that it is stored in a contiguous manner, and try again:
```python
z_t = torch.arange(12).reshape(3,4).t()
print(z_t.contiguous().view(2,6))

tensor([[ 0, 4, 8, 1, 5, 9],  
		[ 2, 6, 10, 3, 7, 11]])```

Alternatively, you can just use the method `reshape()`, which `view()`s when it can, and otherwise calls `contiguous()` and then `view()`:
```python
print(z_t.reshape(2,6))

tensor([[ 0, 4, 8, 1, 5, 9],  
		[ 2, 6, 10, 3, 7, 11]])
```

Lastly, if `z.shape = (3,4)`,  `z.t() != z.view(4,3)` because `.view()` does a _shift_ along the contiguous dimensions, and transposing is... not that. For some reason I made the mistake of assuming that there's only ONE way of reshaping an array of size `(x,y)` into an array of size `(y,x)`, perhaps because in ML theory transposes show up so often, but that's just not the case, so don't be a goof like me:
```python
z = torch.arange(12).reshape(3,4)
print(z)

tensor([[ 0, 1, 2, 3],  
		[ 4, 5, 6, 7],  
		[ 8, 9, 10, 11]])

print(z.t())

tensor([[ 0, 4, 8],  
		[ 1, 5, 9],  
		[ 2, 6, 10],  
		[ 3, 7, 11]])

print(z.view(4,3))
tensor([[ 0, 1, 2],  
		[ 3, 4, 5],  
		[ 6, 7, 8],  
		[ 9, 10, 11]])
```

*Originally Published Mar 16, 2022*