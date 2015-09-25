#include "Python.h"
#include <time.h>
#include <math.h>

static char nanosleep__doc__ [] = "nanosleep module for python2.4";

static int
floatsleep(double secs)
{
	struct timespec t;
	double frac;
	frac = fmod(secs, 1.0);
	secs = floor(secs);

	t.tv_sec = (time_t)secs;
	t.tv_nsec = (long)(frac*1000000000.0);

	Py_BEGIN_ALLOW_THREADS
	if(nanosleep(&t, (struct timespec *)0) != 0){
		if (errno != EINTR) {
			Py_BLOCK_THREADS
			PyErr_SetFromErrno(PyExc_IOError);
			return -1;
		}
	}
	Py_END_ALLOW_THREADS

	return 0;
}

static PyObject *
nanosleep_nanosleep(PyObject *self, PyObject *args)
{
        double secs;
        if (!PyArg_ParseTuple(args, "d:sleep", &secs))
                return NULL;
        if (floatsleep(secs) != 0)
                return NULL;
        Py_INCREF(Py_None);
        return Py_None;
}



static PyMethodDef nanosleep_methods[] = {
	{"nanosleep", nanosleep_nanosleep, METH_VARARGS, "Nanosleep."},
	{NULL,        NULL,                0,            NULL}		/* sentinel */
};

PyMODINIT_FUNC

initnanosleep(void)
{
	Py_InitModule4("nanosleep", nanosleep_methods, nanosleep__doc__,
                       (PyObject *)NULL, PYTHON_API_VERSION);
}
