#include <Python.h>
#include <alsa/asoundlib.h>

#define MAX_MIDI_PORTS   512

snd_seq_t *seq_handle;
char* seq_name;

int in_ports[MAX_MIDI_PORTS], out_ports[MAX_MIDI_PORTS];
int in_ports_index = -1;
int out_ports_index = -1;

static PyObject* seq_open(PyObject* self, PyObject* args) {

	if (!PyArg_ParseTuple(args, "s", &seq_name))
		return NULL;

	if (snd_seq_open(&seq_handle, "default", SND_SEQ_OPEN_DUPLEX, 0) < 0) {
		return Py_BuildValue("i", 0);
	}
	snd_seq_set_client_name(seq_handle, seq_name);

	return Py_BuildValue("i", 1);
}

static PyObject* seq_create_input_port(PyObject* self, PyObject* args) {
	char portname[64];

	in_ports_index++;
	sprintf(portname, "Midi Input");

	if ((in_ports[in_ports_index] = snd_seq_create_simple_port(seq_handle, portname,
		SND_SEQ_PORT_CAP_WRITE|SND_SEQ_PORT_CAP_SUBS_WRITE,
		SND_SEQ_PORT_TYPE_APPLICATION)) < 0) {
		return Py_BuildValue("i", 0);
	}

	return Py_BuildValue("i", in_ports_index);
}


static PyObject* seq_create_output_port(PyObject* self, PyObject* args) {
	char *portname;

	out_ports_index++;

	if (!PyArg_ParseTuple(args, "s", &portname))
		return NULL;

	if ((out_ports[out_ports_index] = snd_seq_create_simple_port(seq_handle, portname,
		SND_SEQ_PORT_CAP_READ|SND_SEQ_PORT_CAP_SUBS_READ,
		SND_SEQ_PORT_TYPE_APPLICATION)) < 0) {
		return Py_BuildValue("i", 0);
	}

	return Py_BuildValue("i", out_ports_index);
}

static PyObject* seq_event_input_pending(PyObject* self, PyObject* args) {
	int i;
	i = snd_seq_event_input_pending(seq_handle, 1);
	return Py_BuildValue("i", i);
}

static PyObject* seq_event_input(PyObject* self, PyObject* args) {
	PyObject* python_ev;
	snd_seq_event_t *ev;

	unsigned char type, flags, tag, queue;
	unsigned int time_tick;
	unsigned int time_time_tv_sec;
	unsigned int time_time_tv_nsec;
	unsigned int source_client;
	unsigned int source_port;
	unsigned int dest_client;
	unsigned int dest_port;

	unsigned char data_note_channel;
	unsigned char data_note_note;
	unsigned char data_note_velocity;
	unsigned char data_note_off_velocity;
	unsigned int data_note_duration;

	unsigned char data_control_channel;
	//unsigned char data_control_unused[3];
	unsigned int data_control_param;
	signed int data_control_value;

	/*unsigned char data_raw8_d [12];
	unsigned int data_raw32_d [3];

	unsigned int data_ext_len;
	void * data_ext_ptr;*/

	
	snd_seq_event_input(seq_handle, &ev);
	snd_seq_ev_set_subs(ev);  
	snd_seq_ev_set_direct(ev);

	type = ev->type;
	flags = ev->flags;
	tag = ev->tag;
	queue = ev->queue;

	time_tick = ev->time.tick;
	time_time_tv_sec = ev->time.time.tv_sec;
	time_time_tv_nsec = ev->time.time.tv_nsec;

	source_client = ev->source.client;
	source_port = ev->source.port;

	dest_client = ev->dest.client;
	dest_port = ev->dest.port;

	data_note_channel = ev->data.note.channel;
	data_note_note = ev->data.note.note;
	data_note_velocity = ev->data.note.velocity;
	data_note_off_velocity = ev->data.note.off_velocity;
	data_note_duration = ev->data.note.duration;

	data_control_channel = ev->data.control.channel;
	//data_control_unused = ev->data.control.unused;
	data_control_param = ev->data.control.param;
	data_control_value = ev->data.control.value;

	python_ev = Py_BuildValue("{s:i,s:i,s:i,s:i,s:{s:i,s:{s:i,s:i}},s:{s:i,s:i},s:{s:i,s:i},s:{s:{s:i,s:i,s:i,s:i,s:i},s:{s:i,s:i,s:i}}}",

		"type",type,
		"flags",flags,
		"tag",tag,
		"queue",queue,
		"time",
			"tick",time_tick,
			"time",
				"tv_sec", time_time_tv_sec,
				"tv_nsec", time_time_tv_nsec,
		"source",
			"client", source_client,
			"port", source_port,
		
		"dest",
			"client", dest_client,
			"port", dest_port,
		"data",
			"note",
				"channel", data_note_channel,
				"note", data_note_note,
				"velocity", data_note_velocity,
				"off_velocity", data_note_off_velocity,
				"duration", data_note_duration,
			"control",
				"channel", data_control_channel,
				"param", data_control_param,
				"value", data_control_value
	);
	snd_seq_free_event(ev);
	return python_ev;
}

static PyObject* seq_event_output(PyObject* self, PyObject* args) {
	snd_seq_event_t ev;

	int port;

	unsigned int type, flags, tag, queue;
	unsigned int time_tick;
	unsigned int time_time_tv_sec;
	unsigned int time_time_tv_nsec;
	unsigned int source_client;
	unsigned int source_port;
	unsigned int dest_client;
	unsigned int dest_port;

	unsigned int data_note_channel;
	unsigned int data_note_note;
	int data_note_velocity;
	unsigned int data_note_off_velocity;
	unsigned int data_note_duration;

	unsigned int data_control_channel;
	//unsigned char data_control_unused[3];
	unsigned int data_control_param;
	signed int data_control_value;

	if (!PyArg_ParseTuple(args, "iiiiiiiiiiiiiiiiiiii", 
		&port,
		&type,
		&flags,
		&tag,
		&queue,
		&time_tick,
		&time_time_tv_sec,
		&time_time_tv_nsec,
		&source_client,
		&source_port,
		&dest_client,
		&dest_port,
		&data_note_channel,
		&data_note_note,
		&data_note_velocity,
		&data_note_off_velocity,
		&data_note_duration,
		&data_control_channel,
		&data_control_param,
		&data_control_value
	)) return NULL;

        snd_seq_ev_clear(&ev);
	snd_seq_ev_set_source(&ev, out_ports[port]);
        snd_seq_ev_set_subs(&ev);
        snd_seq_ev_set_direct(&ev);

	ev.type = type;
	ev.flags = flags;
	ev.tag = tag;
	ev.queue = queue;

	ev.time.tick = time_tick;
	ev.time.time.tv_sec = time_time_tv_sec;
	ev.time.time.tv_nsec = time_time_tv_nsec;

	ev.data.note.channel = data_note_channel;
	ev.data.note.note = data_note_note;
	ev.data.note.velocity = data_note_velocity;
	ev.data.note.off_velocity = data_note_off_velocity;
	ev.data.note.duration = data_note_duration;

	ev.data.control.channel = data_control_channel;
	ev.data.control.param = data_control_param;
	ev.data.control.value = data_control_value;
	
	snd_seq_event_output_direct(seq_handle, &ev);

	return Py_BuildValue("i", 1);
}

static PyObject* seq_event_type_values(PyObject* self, PyObject* args) {
	return Py_BuildValue("[i,i,i,i]", SND_SEQ_EVENT_NOTEON, SND_SEQ_EVENT_NOTEOFF,SND_SEQ_EVENT_CONTROLLER,SND_SEQ_EVENT_PITCHBEND);
}

static PyMethodDef alsamidi_methods[] = {
	{"seq_open", seq_open, METH_VARARGS, "Opens Sequence Handle."},
	{"seq_create_input_port", seq_create_input_port, METH_VARARGS, "Opens Input Port."},
	{"seq_create_output_port", seq_create_output_port, METH_VARARGS, "Opens Output Port."},
	{"seq_event_input_pending", seq_event_input_pending, METH_VARARGS, "Tells when you have pending input events."},
	{"seq_event_input", seq_event_input, METH_VARARGS, "Get input event."},
	{"seq_event_output", seq_event_output, METH_VARARGS, "Send output event."},
	{"seq_event_type_values", seq_event_type_values, METH_VARARGS, "Get Event Types."},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC

initalsamidi(void) {
	(void) Py_InitModule("alsamidi", alsamidi_methods);
}
