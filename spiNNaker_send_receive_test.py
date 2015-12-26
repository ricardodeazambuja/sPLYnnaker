# Don't forget to properly setup:
# /home/simulators/.spynnaker.cfg and /usr/local/lib/python2.7/dist-packages/spynnaker/spynnaker.cfg

import spynnaker.pyNN as sim
import spynnaker_external_devices_plugin.pyNN as ExternalDevices
import spinnman.messages.eieio.eieio_type as eieio_type

# Base code from:
# http://spinnakermanchester.github.io/2015.005.Arbitrary/workshop_material/

sim.setup(timestep=1.0, min_delay=1.0, max_delay=144.0)

num_of_neurons = 2560


# Parameter of the neuron model LIF with exponential currents
cell_params_lif = {'cm'        : 0.25,  # nF
                   'i_offset'  : 0.0,
                   'tau_m'     : 2.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E' : 1.0,
                   'tau_syn_I' : 1.0,
                   'v_reset'   : -70.0,
                   'v_rest'    : -65.0,
                   'v_thresh'  : -50.0
                  }

# Creates a population that will be sending the spikes through the ethernet
pop_out = sim.Population(num_of_neurons, sim.IF_curr_exp,
                         cell_params_lif, label='spikes_out')


cell_params_spike_injector = {
    # The port on which the spiNNaker machine should listen for packets.
    # Packets to be injected should be sent to this port on the spiNNaker
    # machine
    'port': 12346
}

# Creates a population that will receive spikes from the ethernet
# The label value is important as it will be used to find the association 
# between neuron index and SpiNNaker key inside the database file created
# when the board is programmed.
pop_in = sim.Population(num_of_neurons,
                        ExternalDevices.SpikeInjector,
                        cell_params_spike_injector, label='spikes_in')


# Sets up the board to send all the spikes generated by pop_out to the IP=host (and port)
ExternalDevices.activate_live_output_for(pop_out, port=12345, host='192.169.110.2',
                                         use_prefix=False, key_prefix=None, prefix_type=None,
                                         message_type=eieio_type.EIEIOType.KEY_32_BIT, payload_as_time_stamps=False,
                                         use_payload_prefix=False, payload_prefix=None)


# Value used to interconnect the neuron populations (x1E-9)
weight_to_spike = 20.0

# Connects the populations pop_in and pop_out (creates the synapses)
sim.Projection(pop_in, pop_out,
               sim.OneToOneConnector(weights=weight_to_spike))
               # sim.AllToAllConnector(weights=weight_to_spike))


# Initialises the membrane voltage (x1E-3) for the neurons in pop_out
pop_out.initialize("v", [0]*nNeurons)


# Starts the simulation inside SpiNNaker and runs it forever
sim.run()