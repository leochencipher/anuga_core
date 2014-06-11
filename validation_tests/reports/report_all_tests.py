\documentclass[11pt,a4paper]{report}

\usepackage{graphicx}
\usepackage{epstopdf}
\usepackage[section]{placeins} % 'one-shot' command to nicely place figures
\usepackage{datatool}
\usepackage{hyperref}
\usepackage{url}
\usepackage{amsmath}
\DeclareUrlCommand\UScore{\urlstyle{rm}}


\input{local-defs}
\input{saved_parameters}

%=========================================
\begin{document} 
%=========================================

\title{Automated Report on the Performance of \anuga{} on Various Test Problems}
\author{Sudi Mungkasi, Stephen Roberts, Gareth Davies, Rudy vanDrie}    %Type your name(s) here! 
\maketitle
\tableofcontents

%======================
\chapter{Introduction}
%======================
\anuga{} is a free and open source software developed by Roberts and collaborators from the Australian
National University (ANU) and Geoscience Australia (GA). It is devoted to fluid flow simulations,
especially shallow water flows, such as floods, tsunamis and dam breaks. The official website of
\anuga{} is \verb http://anuga.anu.edu.au .



The method implemented in \anuga{} is a numerical finite volume method used to
solve the shallow water equations. Some mathematical explanation of the method
is given in the \anuga{} User Manual~\cite{RNGS2010}. In two dimensions, the
domain is discretised into finite number of triangular elements. \anuga{}
then evolves the conserved quantities (water depth and momenta) with respect
to time to obtain the numerical solution to a given problem. The evolution
is based on the given quantity and flux values. The numerical flux used in
\anuga{} is the Kurganov's flux~\cite{KNP2001, KL2002}. The boundary conditions
that we use in this work include reflective, transmissive, Dirichlet
and time boundaries.


The results in this report were produced by \anuga{} version \majorR{} from svn
repository revision \minorR{} at time \timeR.
The flow algorithm was \alg{} and CFL condition \cfl, unless otherwise stated explicitly. Based   on this version, 26 tests are available in the subversion. To get an automated report, we can run either an individual run of the available tests or the complete (whole) test.

To do an individual test, we can run the python module \\
\verb produce_results.py \\
available in the corresponding test directory. The module will do the numerical simulation of the given problem, plot the simulation results in png files, and type-set the corresponding individual automated report. The individual automated report is in pdf file and saved in the same directory.

To do the complete test, we can just run the python module \\
\verb produce_results.py \\
available in the directory \\
\verb anuga_validation_tests \\
Similar to the module for an individual test, this python module will do the numerical simulations of all the given problems, plot results in png files and save them in its corresponding directory, and finally type-set the complete report. The complete automated report is saved in this directory.

The simulation results can be analysed qualitatively and quantitatively. Qualitative analysis can be done by investigating the plots of the results whether they are physical or not, and whether the behaviour is the same as we expected. Quantitative analysis can be conducted by checking the numerical error. We have provided python module with the name begun by the word ``validate'' in each of individual tests. We can also run validate$\_$all.py to measure the numerical errors from the directory \verb anuga_validation_tests . This validate$\_$all.py will run a subset of the available tests having sensible ``correct'' results to test against.

The main parameters in the validations are the Courant--Friedrichs-Lewy (CFL) number and the flow algorithm. They are spelled ``cfl'' and ``alg'' respectively in the python module \\
\verb parameters.py \\
which is available in the \\
\verb anuga_validation_tests \\
directory. In the default setting, we set the CFL to be $1.0$ and the flow algorithm to be 1$\_$5 (second order in space and first order in time). The complete available flow algorithms are as follow:
'1$\_$0', '1$\_$5', '1$\_$75', '2$\_$0', '2$\_$0$\_$limited', '2$\_$5', 'tsunami', 'yusuke'.
%\begin{enumerate}
%\item '1$\_$0', 
%\item '1$\_$5', 
%\item '1$\_$75', 
%\item '2$\_$0', 
%\item '2$\_$0$\_$limited', 
%\item '2$\_$5', 
%\item 'tsunami', 
%\item 'yusuke'.
%\end{enumerate}
They can be found in \\
\verb \anuga_core\source\anuga\shallow_water\shallow_water_domain.py .



The report is organised as follows. We collect a number of tests against
analytical exact solutions in Chapter~\ref{ch:ana}. Tests against other
reference data or solutions are given in Chapter~\ref{ch:ref}.
We provide explanations on how to add new tests in the Appendix.

%======================
\chapter{Tests against analytical exact solutions} \label{ch:ana}
%======================

\inputresults{analytical_exact/dam_break_dry}
\inputresults{analytical_exact/dam_break_wet}
\inputresults{analytical_exact/avalanche_dry}
\inputresults{analytical_exact/avalanche_wet}
\inputresults{analytical_exact/carrier_greenspan_periodic}
\inputresults{analytical_exact/carrier_greenspan_transient}
\inputresults{analytical_exact/deep_wave}
\inputresults{analytical_exact/mac_donald_short_channel}
\inputresults{analytical_exact/parabolic_basin}
\inputresults{analytical_exact/paraboloid_basin}

\inputresults{analytical_exact/runup_on_beach}
\inputresults{analytical_exact/runup_on_sinusoid_beach}
\inputresults{analytical_exact/landslide_tsunami}

\inputresults{analytical_exact/lake_at_rest_immersed_bump}
\inputresults{analytical_exact/lake_at_rest_steep_island}
\inputresults{analytical_exact/river_at_rest_varying_topo_width}
\inputresults{analytical_exact/rundown_mild_slope}
\inputresults{analytical_exact/rundown_mild_slope_coarse}
\inputresults{analytical_exact/subcritical_over_bump}
\inputresults{analytical_exact/transcritical_with_shock}
\inputresults{analytical_exact/transcritical_without_shock}
\inputresults{analytical_exact/trapezoidal_channel}

%%======================
\chapter{Tests against reference data or solutions} \label{ch:ref}
%%======================
\inputresults{experimental_data/dam_break_yeh_petroff}
\inputresults{behaviour_only/lid_driven_cavity}

\inputresults{other_references/radial_dam_break_dry}
\inputresults{other_references/radial_dam_break_wet}

\inputresults{case_studies/okushiri}


%======================
\appendix
%======================
%======================
\chapter{Adding New Tests}
%======================


To setup a new validation test, create a test directory under the
\textsc{Tests} directory. In that directory there should be the test code, a
\TeX{} file \texttt{results.tex} and a python script
\texttt{produce\_results.py}, which runs the simulation and produces the
outputs. Copy the format from the other test directory. 

In this \TeX{} file, \texttt{report.tex}, add a line
\begin{verbatim}
\inputresults{Tests/Directory/Name}
\end{verbatim}



\section{Algorithm Parameters}
Note that parameters can be communicated from the \verb|local_parameters.py|
file in the \verb|anuga_validation_tests| directory. If there is no file
\verb|local_parameters.py| then the parameters are taken from the
\verb|parameters.py| file. You should not change this file.

In particular the
values of \verb|alg| (flow algorithm) and \verb|cfl| (CFL Condition)
are passed as command options when calling \verb|produce_results.py| in the
test directories.

You can pass though the parameters straight from the \verb|parameters.py| file as follows
\begin{verbatim}
from anuga_validation_tests.parameters import alg
from anuga_validation_tests.parameters import cfl
\end{verbatim}

\section{Generic form of \texttt{produce\_results.py}}

The \texttt{produce\_results.py} files in the test directories should have the
following general form

\begin{verbatim}
from anuga_validation_test_utilities.fabricate import *
from anuga_validation_test_utilities import run_validation_script

# Setup the python scripts which produce the output for this
# validation test
def build():
    run_validation_script('run_problem.py')
    run_validation_script('plot_problem.py')
    run('python','latex_report.py')
    pass

def clean():
    autoclean()

main()
\end{verbatim}
This script uses \texttt{fabricate} which automatically determines dependences
and only runs the command if the parameters alg and cfl have changed,
or input/output or source files have changed. (\texttt{fabricate} is a replacement for
standard \texttt{make})


%======================
% bibliography
%======================

\bibliographystyle{plain}
\bibliography{bibliography}

\end{document}