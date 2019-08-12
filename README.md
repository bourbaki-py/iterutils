# Table of Contents

1. [How to use this Module](#intro)
2. [Contributing](#contribute)

# <a name="intro"></a> How to use this Module

Let's say you have some data like this:

<pre><code>
>>> import pandas as pd
>>> import numpy as np
>>> df = pd.DataFrame(np.arange(10*3).reshape(10,3), columns=["a", "b", "c"])
>>> print(df)<br/>
    a   b   c
0   0   1   2
1   3   4   5
2   6   7   8
3   9  10  11
4  12  13  14
5  15  16  17
6  18  19  20
7  21  22  23
8  24  25  26
9  27  28  29
</code></pre>

If you've ever written code like this (most likely on *several* occasions):

<pre><code>
>>> chunksize = 3
>>> nchunks = df.shape[0] // chunksize
>>> if df.shape[0] % chunksize != 0:
>>>     nchunks += 1
>>>
>>> for i in range(nchunks):
>>>     chunk = df.iloc[chunksize*i:chunksize*(i+1)]
>>>     # do something with `chunk`
>>>     print(chunk, end='\n')<br/>
   a  b  c
0  0  1  2
1  3  4  5
2  6  7  8<br/>
    a   b   c
3   9  10  11
4  12  13  14
5  15  16  17<br/>
    a   b   c
6  18  19  20
7  21  22  23
8  24  25  26<br/>
    a   b   c
9  27  28  29
</code></pre>

Then this module is for you!
After you install this package, you can accomplish the same task by writing instead: 

<pre><code>
>>> from bourbaki.iterutils import batched
>>>
>>> for chunk in batched(df, 3):
>>>    # do something with chunk
>>>    print(chunk, end='\n')
</code></pre>

To produce the same results.

In addition to `batched`, there is `even_batched`, which will do this if you for some reason need chunks with sizes all 
equal to `n` or `n+1` for some `n`:

<pre><code>
>>> from bourbaki.iterutils import even_batched
>>>
>>> for chunk in even_batched(df, nchunks=3):
>>>    # do something with chunk
>>>    print(chunk, end='\n')<br/>
   a   b   c
0  0   1   2
1  3   4   5
2  6   7   8
3  9  10  11<br/>
    a   b   c
4  12  13  14
5  15  16  17
6  18  19  20<br/>
    a   b   c
7  21  22  23
8  24  25  26
9  27  28  29
</code></pre>

You can batch just about any iterable, iterator, or sliceable collection - I demonstrate `pandas.DataFrame` here because 
it shows off the extensibility of this module: the naive slice operation, `df[a:b]` doesn't behave as you would expect; 
you have to access integer-row slices with the `df.iloc` accessor to achieve the desired result.

If you have your own collection type that `iterutils` doesn't as yet know how to slice into chunks, you do this (
with `pandas.DataFrame` as an example case):

<pre><code>
from bourbaki.iterutils import to_sliceable
to_sliceable.register(pd.DataFrame, lambda df: df.iloc)
</code></pre>

Or if you have a collection that is simply integer-sliceable already and `iterutils` just doesn't know about it yet, 
simply:

<pre><code>
from bourbaki.iterutils import Sliceable
Sliceable.register(np.ndarray)
</code></pre>

(Numpy arrays are already registered, but this is how you would do it with another collection type)

Finally, if what you have is a generator or iterator such as a `map` or `filter` which isn't sliceable but only iterable,
and you just want to break it into pieces without boilerplate, you can just use `batched` without worrying about 
registering any types. You can also use `even_batched`, but only if you know the total length of the iterator and pass 
it to the `len_=` keyword arg, which is necessary to compute the chunk size.

Note that in the case of types which are not known to be `Sliceable` or coercible to a sliceable view via `to_sliceable`,
you will always get an iterator of simple `list`s back from `batched` or `even_batched`; the default behavior in that 
case is just to iterate over the collection and collect the chunks dynamically into lists.
So the advantage of registering a type as sliceable is not only computational (less memory overhead and lower runtime 
due to less copying), but also semantic - you can ensure that the type of your chunks is the same as the type of the 
collection being chunked by specifying how the slicing will be performed.

# <a name="contribute"></a> Contributing

See something missing here that you think should be added?
Put in a pull request or contact the maintainer!

[Matthew Hawthorn](hawthorn.matthew@gmail.com)
