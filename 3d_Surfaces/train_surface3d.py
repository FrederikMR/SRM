# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 22:06:08 2021

@author: Frederik
"""

#%% Sources

"""
Sources:
https://debuggercafe.com/getting-started-with-variational-autoencoder-using-pytorch/
http://adamlineberry.ai/vae-series/vae-code-experiments
https://gist.github.com/sbarratt/37356c46ad1350d4c30aefbd488a4faa
https://discuss.pytorch.org/t/cpu-ram-usage-increasing-for-every-epoch/24475/10
https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html
"""

#%% Modules

import torch
import torch.optim as optim
from torch.utils.data import DataLoader
import argparse
import pandas as pd

#Own files
from VAE_surface3d import VAE_3d

#%% Parser for command line arguments

def parse_args():
    parser = argparse.ArgumentParser()
    # File-paths
    parser.add_argument('--data_path', default='Data/para_data.csv', # 'Data/surface_R2.csv'
                        type=str)
    parser.add_argument('--save_model_path', default='trained_models/para_3d', #'trained_models/surface_R2.pt'
                        type=str)
    parser.add_argument('--save_step', default=100,
                        type=int)

    #Hyper-parameters
    parser.add_argument('--device', default='cpu', #'cuda:0'
                        type=str)
    parser.add_argument('--epochs', default=10, #100000
                        type=int)
    parser.add_argument('--batch_size', default=100,
                        type=int)
    parser.add_argument('--lr', default=0.0001,
                        type=float)


    args = parser.parse_args()
    return args

#%% Main loop

def main():

    args = parse_args()
    train_loss_elbo = [] #Elbo loss
    train_loss_rec = [] #Reconstruction loss
    train_loss_kld = [] #KLD loss
    epochs = args.epochs

    df = pd.read_csv(args.data_path, index_col=0)
    DATA = torch.Tensor(df.values)
    DATA = torch.transpose(DATA, 0, 1)

    if args.device == 'cpu':
        trainloader = DataLoader(dataset = DATA, batch_size= args.batch_size,
                                 shuffle = True, pin_memory=True, num_workers = 0)
    else:
        trainloader = DataLoader(dataset = DATA, batch_size= args.batch_size,
                                 shuffle = True, pin_memory=True, num_workers=2)
    N = len(trainloader.dataset)

    model = VAE_3d().to(args.device)

    optimizer = optim.SGD(model.parameters(), lr=args.lr)

    model.train()
    for epoch in range(epochs):
        running_loss_elbo = 0.0
        running_loss_rec = 0.0
        running_loss_kld = 0.0
        for x in trainloader:
            x = x.to(args.device)
            _, x_hat, mu, var, kld, rec_loss, elbo = model(x)
            optimizer.zero_grad(set_to_none=True) #Based on performance tuning
            elbo.backward()
            optimizer.step()

            running_loss_elbo += elbo.item()
            running_loss_rec += rec_loss.item()
            running_loss_kld += kld.item()

            #del x, x_hat, mu, var, kld, rec_loss, elbo #In case you run out of memory

        train_epoch_loss = running_loss_elbo/N
        train_loss_elbo.append(train_epoch_loss)
        train_loss_rec.append(running_loss_rec/N)
        train_loss_kld.append(running_loss_kld/N)
        print(f"Epoch {epoch+1}/{epochs} - loss: {train_epoch_loss:.4f}")
        
        
        if (epoch+1) % args.save_step == 0:
            checkpoint = args.save_model_path+'_epoch_'+str(epoch+1)+'.pt'
            torch.save({'epoch': epoch+1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'ELBO': train_loss_elbo,
                'rec_loss': train_loss_rec,
                'KLD': train_loss_kld
                }, checkpoint)


    checkpoint = args.save_model_path+'_epoch_'+str(epoch+1)+'.pt'
    torch.save({'epoch': epoch+1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'ELBO': train_loss_elbo,
                'rec_loss': train_loss_rec,
                'KLD': train_loss_kld
                }, checkpoint)

    return

#%% Calling main

if __name__ == '__main__':
    main()
