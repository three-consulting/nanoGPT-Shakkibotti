# train a miniature character-level shakespeare model
# good for debugging and playing on macbooks and such

out_dir = 'out-chess'
eval_interval = 2500 # keep frequent because we'll overfit
eval_iters = 200
log_interval = 10 # don't print too too often

# we expect to overfit on this small dataset, so only save when val improves
always_save_checkpoint = False

wandb_log = False # override via command line if you like
wandb_project = 'chess'
wandb_run_name = 'mini-gpt'

init_from = 'resume'

dataset = 'chess'
gradient_accumulation_steps = 10
batch_size = 64
block_size = 64 # context of up to 256 previous characters

# baby GPT model :)
n_layer = 12
n_head = 64
n_embd = 1024
dropout = 0.1

learning_rate = 1e-7 # with baby networks can afford to go a bit higher
max_iters = 5000000
lr_decay_iters = 5000000 # make equal to max_iters usually
min_lr = 1e-8 # learning_rate / 10 usually
beta2 = 0.99 # make a bit bigger because number of tokens per iter is small

warmup_iters = 100 # not super necessary potentially

# on macbook also add
# device = 'cpu'  # run on cpu only
# compile = False # do not torch compile the model
