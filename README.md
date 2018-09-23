# sPLYnnaker
sPLYnnaker is a collection of tools in Python I'm creating to be able to play with [SpiNNaker](https://github.com/SpiNNakerManchester) sending and receiving spikes using ethernet.  
### Useful command line *spells*:  
Verifies the PID of the process using the port (e.g. 8080):  
sudo lsof -i :8080  
  
Makes the default route the SpiNN-? board IP (the only way I've found to send and receive spikes using OSX after the board was programmed using Ubuntu):  
sudo route -nv delete 0.0.0.0  
sudo route -nv add 0.0.0.0 192.169.110.2  


http://ricardodeazambuja.com/
