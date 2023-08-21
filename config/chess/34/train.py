# train a miniature character-level shakespeare model
# good for debugging and playing on macbooks and such

out_dir = 'out-chess'
eval_interval = 5000 # keep frequent because we'll overfit
eval_iters = 200
log_interval = 10 # don't print too too often
eval_only = False

# we expect to overfit on this small dataset, so only save when val improves
always_save_checkpoint = False

wandb_log = False # override via command line if you like
wandb_project = 'chess'
wandb_run_name = 'mini-gpt'

dataset = 'chess'
gradient_accumulation_steps = 1
batch_size = 128
block_size = 64 # context of up to 256 previous characters

n_layer = 12
n_head = 12
n_embd = 768
dropout = 0.1

learning_rate = 1e-5 # with baby networks can afford to go a bit higher
max_iters = 100000
lr_decay_iters = 100000 # make equal to max_iters usually
min_lr = 1e-6 # learning_rate / 10 usually
beta2 = 0.99 # make a bit bigger because number of tokens per iter is small


bias = False
vocab_size = 588
wandb_log = False
weight_decay = 0.1
beta1 = 0.9
grad_clip = 1.0
decay_lr = True
backend = 'nccl'

warmup_iters = 10 # not super necessary potentially
