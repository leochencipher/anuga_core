""" Random utilities for reading sww file data and for plotting
(in ipython, or in scripts)

    Functionality of note:

    util.get_outputs -- read the data from a single sww file
    into a single object
    
    util.combine_outputs -- read the data from a list of sww
    files into a single object
    
    util.near_transect -- for finding the indices of points
                          'near' to a given line, and
                          assigning these points a
                          coordinate along that line.

    This is useful for plotting outputs which are 'almost' along a
    transect (e.g. a channel cross-section) -- see example below

    util.sort_sww_filenames -- match sww filenames by a wildcard, and order
                               them according to their 'time'. This means that
                               they can be stuck together using
                               'combine_outputs' correctly

    util.triangle_areas -- compute the areas of every triangle
                           in a get_outputs object [ must be vertex-based]

    util.water_volume -- compute the water volume at every
                         time step in an sww file (needs both
                         vertex and centroid value input). 

    util.Make_Geotiff -- convert sww centroids to a georeferenced tiff
 
    Here is an example ipython session which uses some of these functions:

    > import util
    > from matplotlib import pyplot as pyplot
    > p=util.get_output('myfile.sww',minimum_allowed_height=0.01)
    > p2=util.get_centroids(p,velocity_extrapolation=True)
    > xxx=util.near_transect(p,[95., 85.], [120.,68.],tol=2.) # Could equally well use p2
    > pyplot.ion() # Interactive plotting
    > pyplot.scatter(xxx[1],p.vel[140,xxx[0]],color='red') # Plot along the transect

    FIXME: TODO -- Convert to a single function 'get_output', which can either take a
          single filename, a list of filenames, or a wildcard defining a number of
          filenames, and ensure that in each case, the output will be as desired.

"""
from anuga.file.netcdf import NetCDFFile
import numpy
import copy

class combine_outputs:
    """
    Read in a list of filenames, and combine all their outputs into a single object.
    e.g.:

    p = util.combine_outputs(['file1.sww', 'file1_time_10000.sww', 'file1_time_20000.sww'], 0.01)
    
    will make an object p which has components p.x,p.y,p.time,p.stage, .... etc,
    where the values of stage / momentum / velocity from the sww files are concatenated as appropriate.

    This is nice for interactive interrogation of model outputs, or for sticking together outputs in scripts
   
    WARNING: It is easy to use lots of memory, if the sww files are large.

    Note: If you want the centroid values, then you could subsequently use:

    p2 = util.get_centroids(p,velocity_extrapolation=False)

    which would make an object p2 that is like p, but holds information at centroids
    """
    def __init__(self, filename_list, minimum_allowed_height=1.0e-03, verbose=False):
        #
        # Go through the sww files in 'filename_list', and combine them into one object.
        #

        for i, filename in enumerate(filename_list):
            if verbose: print i, filename
            # Store output from filename
            p_tmp = get_output(filename, minimum_allowed_height,verbose=verbose)
            if(i==0):
                # Create self
                p1=p_tmp
            else:
                # Append extra data to self
                # Note that p1.x, p1.y, p1.vols, p1.elev should not change
                assert (p1.x == p_tmp.x).all()
                assert (p1.y == p_tmp.y).all()
                assert (p1.vols ==p_tmp.vols).all()
                p1.time = numpy.append(p1.time, p_tmp.time)
                p1.stage = numpy.append(p1.stage, p_tmp.stage, axis=0)
                p1.height = numpy.append(p1.height, p_tmp.height, axis=0)
                p1.xmom = numpy.append(p1.xmom, p_tmp.xmom, axis=0)
                p1.ymom = numpy.append(p1.ymom, p_tmp.ymom, axis=0)
                p1.xvel = numpy.append(p1.xvel, p_tmp.xvel, axis=0)
                p1.yvel = numpy.append(p1.yvel, p_tmp.yvel, axis=0)
                p1.vel = numpy.append(p1.vel, p_tmp.vel, axis=0)
        
        self.x, self.y, self.time, self.vols, self.stage, \
                self.height, self.elev, self.friction, self.xmom, self.ymom, \
                self.xvel, self.yvel, self.vel, self.minimum_allowed_height,\
                self.xllcorner, self.yllcorner, self.timeSlices =\
                p1.x, p1.y, p1.time, p1.vols, p1.stage, \
                p1.height, p1.elev, p1.friction, p1.xmom, p1.ymom, \
                p1.xvel, p1.yvel, p1.vel, p1.minimum_allowed_height,\
                p1.xllcorner, p1.yllcorner, p1.timeSlices 

        self.filename = p1.filename
        self.verbose = p1.verbose


####################

def sort_sww_filenames(sww_wildcard):
    # Function to take a 'wildcard' sww filename, 
    # and return a list of all filenames of this type,
    # sorted by their time.
    # This can then be used efficiently in 'combine_outputs'
    # if you have many filenames starting with the same pattern
    import glob
    filenames=glob.glob(sww_wildcard)
    
    # Extract time from filenames
    file_time=range(len(filenames)) # Predefine
     
    for i,filename in enumerate(filenames):
        filesplit=filename.rsplit('_time_')
        if(len(filesplit)>1):
            file_time[i]=int(filesplit[1].split('_0.sww')[0])
        else:
            file_time[i]=0         
    
    name_and_time=zip(file_time,filenames)
    name_and_time.sort() # Sort by file_time
    
    output_times, output_names = zip(*name_and_time)
    
    return list(output_names)

#####################################################################
class get_output:
    """Read in data from an .sww file in a convenient form
       e.g. 
        p = util.get_output('channel3.sww', minimum_allowed_height=0.01)
        
       p then contains most relevant information as e.g., p.stage, p.elev, p.xmom, etc 
    """
    def __init__(self, filename, minimum_allowed_height=1.0e-03, timeSlices='all', verbose=False):
                # FIXME: verbose is not used
        self.x, self.y, self.time, self.vols, self.stage, \
                self.height, self.elev, self.friction, self.xmom, self.ymom, \
                self.xvel, self.yvel, self.vel, self.minimum_allowed_height,\
                self.xllcorner, self.yllcorner, self.timeSlices = \
                read_output(filename, minimum_allowed_height,copy.copy(timeSlices))
        self.filename = filename
        self.verbose = verbose

####################################################################
def getInds(varIn, timeSlices, absMax=False):
    """
     Convenience function to get the indices we want in an array.
     There are a number of special cases that make this worthwhile
     having in its own function
    
     INPUT: varIn -- numpy array, either 1D (variables in space) or 2D
            (variables in time+space)
            timeSlices -- times that we want the variable, see read_output or get_output
            absMax -- if TRUE and timeSlices is 'max', then get max-absolute-values
     OUTPUT:
           
    """
    var=copy.copy(varIn) # avoid python pointer issues
    if (len(varIn.shape)==2):
        # Get particular time-slices, unless the variable is constant
        # (e.g. elevation is often constant)
        if timeSlices is 'max':
            # Extract the maxima over time, assuming there are multiple
            # time-slices, and ensure the var is still a 2D array
            if( not absMax):
                var=var.max(axis=0)
            else:
                # For variables xmom,ymom,xvel,yvel we want the 'maximum-absolute-value'
                # We could do this everywhere, but I assume the loop is a bit slower
                varInds=abs(var).argmax(axis=0)
                varNew=varInds*0.
                for i in range(len(varInds)):
                    varNew[i] = var[varInds[i],i]
                #var=[var[varInds[i],i] for i in varInds]
                var=varNew
            var=var.reshape((1,len(var)))
        else:
            var=var[timeSlices,:]
    
    return var

############################################################################

def read_output(filename, minimum_allowed_height, timeSlices):
    """
     Purpose: To read the sww file, and output a number of variables as arrays that 
              we can then e.g. plot, interrogate 

              See get_output for the typical interface, and get_centroids for
                working with centroids directly
    
     Input: filename -- The name of an .sww file to read data from,
                        e.g. read_sww('channel3.sww')
            minimum_allowed_height -- zero velocity when height < this
            timeSlices -- List of time indices to read (e.g. [100] or [0, 10, 21]), or 'all' or 'last' or 'max'
                          If 'max', the time-max of each variable will be computed. For xmom/ymom/xvel/yvel, the
                           one with maximum magnitude is reported
    
    
     Output: x, y, time, stage, height, elev, xmom, ymom, xvel, yvel, vel
             x,y are only stored at one time
             elevation may be stored at one or multiple times
             everything else is stored every time step for vertices
    """

    # Import modules



    # Open ncdf connection
    fid=NetCDFFile(filename)
    
    time=fid.variables['time'][:]

    # Treat specification of timeSlices
    if(timeSlices=='all'):
        inds=range(len(time))
    elif(timeSlices=='last'):
        inds=[len(time)-1]
    elif(timeSlices=='max'):
        inds='max' #
    else:
        try:
            inds=list(timeSlices)
        except:
            inds=[timeSlices]
    
    if(inds is not 'max'):
        time=time[inds]
    else:
        # We can't really assign a time to 'max', but I guess max(time) is
        # technically the right thing -- if not misleading
        time=time.max()

    
    # Get lower-left
    xllcorner=fid.xllcorner
    yllcorner=fid.yllcorner

    # Read variables
    x=fid.variables['x'][:]
    y=fid.variables['y'][:]

    stage=getInds(fid.variables['stage'][:], timeSlices=inds)
    elev=getInds(fid.variables['elevation'][:], timeSlices=inds)

    # Simple approach for volumes
    vols=fid.variables['volumes'][:]

    # Friction if it exists
    if(fid.variables.has_key('friction')):
        friction=getInds(fid.variables['friction'][:],timeSlices=inds) 
    else:
        # Set friction to nan if it is not stored
        friction=elev*0.+numpy.nan
    
    #@ Here we get 'all' of height / xmom /ymom
    #@ This could be done using less memory/computation in 
    #@  the case of multiple time-slices

    if(fid.variables.has_key('height')):
        heightAll=fid.variables['height'][:]
    else:
        # Back calculate height if it is not stored
        heightAll=fid.variables['stage'][:]
        if(len(heightAll.shape)==len(elev.shape)):
            heightAll=heightAll-elev
        else:
            for i in range(heightAll.shape[0]):
                heightAll[i,:]=heightAll[i,:]-elev
    heightAll=heightAll*(heightAll>0.) # Height could be negative for tsunami algorithm
    # Need xmom,ymom for all timesteps
    xmomAll=fid.variables['xmomentum'][:]
    ymomAll=fid.variables['ymomentum'][:]

    height=getInds(heightAll, timeSlices=inds) 
    # For momenta, we want maximum-absolute-value events
    xmom=getInds(xmomAll, timeSlices=inds, absMax=True)
    ymom=getInds(ymomAll, timeSlices=inds, absMax=True)

    # velocity requires some intermediate calculation in general
    tmp = xmomAll/(heightAll+1.0e-12)*(heightAll>minimum_allowed_height)
    xvel=getInds(tmp,timeSlices=inds, absMax=True)
    tmp = ymomAll/(heightAll+1.0e-12)*(heightAll>minimum_allowed_height)
    yvel=getInds(tmp,timeSlices=inds, absMax=True)
    tmp = (xmomAll**2+ymomAll**2)**0.5/(heightAll+1.0e-12)*(heightAll>minimum_allowed_height)
    vel=getInds(tmp, timeSlices=inds) # Vel is always >= 0.

    fid.close()

    return x, y, time, vols, stage, height, elev, friction, xmom, ymom,\
           xvel, yvel, vel, minimum_allowed_height, xllcorner,yllcorner, inds

######################################################################################

class get_centroids:
    """
    Extract centroid values from the output of get_output, OR from a
        filename  
    See read_output or get_centroid_values for further explanation of
        arguments
    e.g.
        # Case 1 -- get vertex values first, then centroids
        p = util.get_output('my_sww.sww', minimum_allowed_height=0.01) 
        pc=util.get_centroids(p, velocity_extrapolation=True) 

        # Case 2 -- get centroids directly
        pc=util.get_centroids('my_sww.sww', velocity_extrapolation=True) 

    NOTE: elevation is only stored once in the output, even if it was
          stored every timestep.
           This is done because presently centroid elevations in ANUGA
           do not change over time.  
           Also lots of existing plotting code assumes elevation is a 1D
           array
    """
    def __init__(self,p, velocity_extrapolation=False, verbose=False,
                 timeSlices=None, minimum_allowed_height=1.0e-03):
        
        self.time, self.x, self.y, self.stage, self.xmom,\
             self.ymom, self.height, self.elev, self.friction, self.xvel,\
             self.yvel, self.vel, self.xllcorner, self.yllcorner, self.timeSlices= \
             get_centroid_values(p, velocity_extrapolation,\
                         timeSlices=copy.copy(timeSlices),\
                         minimum_allowed_height=minimum_allowed_height,\
                         verbose=verbose)
                                 

def get_centroid_values(p, velocity_extrapolation, verbose, timeSlices, 
                        minimum_allowed_height):
    """
    Function to get centroid information -- main interface is through 
        get_centroids. 
        See get_centroids for usage examples, and read_output or get_output for further relevant info
     Input: 
           p --  EITHER:
                  The result of e.g. p=util.get_output('mysww.sww'). 
                  See the get_output class defined above. 
                 OR:
                  Alternatively, the name of an sww file
    
           velocity_extrapolation -- If true, and centroid values are not
            in the file, then compute centroid velocities from vertex velocities, and
            centroid momenta from centroid velocities. If false, and centroid values
            are not in the file, then compute centroid momenta from vertex momenta,
            and centroid velocities from centroid momenta
    
           timeSlices = list of integer indices when we want output for, or
                        'all' or 'last' or 'max'. See read_output
    
           minimum_allowed_height = height at which velocities are zeroed. See read_output
    
     Output: Values of x, y, Stage, xmom, ymom, elev, xvel, yvel, vel etc at centroids
    """

    #@ Figure out if p is a string (filename) or the output of get_output
    pIsFile=(type(p) is str)
 
    if(pIsFile): 
        fid=NetCDFFile(p) 
    else:
        fid=NetCDFFile(p.filename)

    # UPDATE: 15/06/2014 -- below, we now get all variables directly from the file
    #         This is more flexible, and allows to get 'max' as well
    #         However, potentially it could have performance penalities vs the old approach (?)

    # Make 3 arrays, each containing one index of a vertex of every triangle.
    vols=fid.variables['volumes'][:]
    vols0=vols[:,0]
    vols1=vols[:,1]
    vols2=vols[:,2]
    
    # Get lower-left offset
    xllcorner=fid.xllcorner
    yllcorner=fid.yllcorner
   
    #@ Get timeSlices 
    # It will be either a list of integers, or 'max'
    l=len(vols)
    time=fid.variables['time'][:]
    nts=len(time) # number of time slices in the file 
    if(timeSlices is None):
        if(pIsFile):
            # Assume all timeSlices
            timeSlices=range(nts)
        else:
            timeSlices=copy.copy(p.timeSlices)
    else:
        # Treat word-based special cases
        if(timeSlices is 'all'):
            timeSlices=range(nts)
        if(timeSlices is 'last'):
            timeSlices=[nts-1]

    #@ Get minimum_allowed_height
    if(minimum_allowed_height is None):
        if(pIsFile):
            minimum_allowed_height=0.
        else:
            minimum_allowed_height=copy.copy(p.minimum_allowed_height)

    # Treat specification of timeSlices
    if(timeSlices=='all'):
        inds=range(len(time))
    elif(timeSlices=='last'):
        inds=[len(time)-1]
    elif(timeSlices=='max'):
        inds='max' #
    else:
        try:
            inds=list(timeSlices)
        except:
            inds=[timeSlices]
    
    if(inds is not 'max'):
        time=time[inds]
    else:
        # We can't really assign a time to 'max', but I guess max(time) is
        # technically the right thing -- if not misleading
        time=time.max()

    # Get coordinates
    x=fid.variables['x'][:]
    y=fid.variables['y'][:]
    x_cent=(x[vols0]+x[vols1]+x[vols2])/3.0
    y_cent=(y[vols0]+y[vols1]+y[vols2])/3.0

    def getCentVar(varkey_c, timeSlices=inds, absMax=False):
        """
            Convenience function, assumes knowedge of 'timeSlices' and vols0,1,2
        """
        if(fid.variables.has_key(varkey_c)==False):
            # It looks like centroid values are not stored
            # In this case, compute centroid values from vertex values
            
            newkey=varkey_c.replace('_c','')
            tmp = fid.variables[newkey][:]
            try: # array contain time slides
                tmp=(tmp[:,vols0]+tmp[:,vols1]+tmp[:,vols2])/3.0
            except:
                tmp=(tmp[vols0]+tmp[vols1]+tmp[vols2])/3.0
            var_cent=getInds(tmp, timeSlices=timeSlices, absMax=absMax)
        else:
            var_cent=getInds(fid.variables[varkey_c][:], timeSlices=timeSlices, absMax=absMax)
        return var_cent

    # Stage and height and elevation
    stage_cent=getCentVar('stage_c', timeSlices=inds)
    elev_cent=getCentVar('elevation_c', timeSlices=inds)

    if(len(elev_cent)==2):
        # Coerce to 1D array, since lots of our code assumes it is
        elev_cent=elev_cent[0,:]

    height_cent=stage_cent*0.
    for i in range(stage_cent.shape[0]):
        height_cent[i,:]=stage_cent[i,:]-elev_cent

    # Friction might not be stored at all
    try:
        friction_cent=getCentVar('friction_c')
    except:
        friction_cent=elev_cent*0.+numpy.nan

    if(fid.variables.has_key('xmomentum_c')):
        # Assume that both xmomentum,ymomentum are stored at centroids
        # Because velocity is back computed, and we might want maxima, 
        # we get all data for convenience
        xmomC=getCentVar('xmomentum_c', timeSlices=range(nts))
        ymomC=getCentVar('ymomentum_c', timeSlices=range(nts))

        # height might not be stored
        try:
            hC = getCentVar('height_c', timeSlices=range(nts))
        except:
            # Compute from stage
            hC = getCentVar('stage_c', timeSlices=range(nts))
            for i in range(hC.shape[0]):
                hC[i,:]=hC[i,:]-elev_cent
            
        xmom_cent = getInds(xmomC*(hC>minimum_allowed_height), timeSlices=inds,absMax=True)
        xvel_cent = getInds(xmomC/(hC+1.0e-06)*(hC>minimum_allowed_height), timeSlices=inds, absMax=True)

        ymom_cent = getInds(ymomC*(hC>minimum_allowed_height), timeSlices=inds,absMax=True)
        yvel_cent = getInds(ymomC/(hC+1.0e-06)*(hC>minimum_allowed_height), timeSlices=inds, absMax=True)

        tmp = (xmomC**2 + ymomC**2)**0.5/(hC+1.0e-06)*(hC>minimum_allowed_height)
        vel_cent=getInds(tmp, timeSlices=inds)
        
    else:
        #@ COMPUTE CENTROIDS FROM VERTEX VALUES
        #@
        #@ Here we get 'all' of height / xmom /ymom
        #@ This could be done using less memory/computation in 
        #@  the case of multiple time-slices
        if(fid.variables.has_key('height')):
            heightAll=fid.variables['height'][:]
        else:
            # Back calculate height if it is not stored
            heightAll=fid.variables['stage'][:]
            elev = fid.variables['elevation'][:]
            if(len(heightAll.shape)==len(elev.shape)):
                heightAll=heightAll-elev
            else:
                for i in range(heightAll.shape[0]):
                    heightAll[i,:]=heightAll[i,:]-elev
        heightAll=heightAll*(heightAll>0.) # Height could be negative for tsunami algorithm
        # Need xmom,ymom for all timesteps
        xmomAll=fid.variables['xmomentum'][:]
        ymomAll=fid.variables['ymomentum'][:]
        
        if velocity_extrapolation:
            # Compute velocity from vertex velocities, then back-compute
            # momentum from that
            tmp = xmomAll/(heightAll+1.0-06)*(heightAll>minimum_allowed_height)
            xvel=(tmp[:,vols0]+tmp[:,vols1]+tmp[:,vols2])/3.0
            htc = (heightAll[:,vols0] + heightAll[:,vols1] + heightAll[:,vols2])/3.0
            xvel_cent=getInds(xvel, timeSlices=inds, absMax=True)
            xmom_cent=getInds(xvel*htc, timeSlices=inds, absMax=True)

            tmp = ymomAll/(heightAll+1.0-06)*(heightAll>minimum_allowed_height)
            yvel=(tmp[:,vols0]+tmp[:,vols1]+tmp[:,vols2])/3.0
            yvel_cent=getInds(yvel, timeSlices=inds, absMax=True)
            ymom_cent=getInds(yvel*htc, timeSlices=inds, absMax=True)
           
            vel_cent=getInds( (xvel**2+yvel**2)**0.5, timeSlices=inds)
            
        else:
            # Compute momenta from vertex momenta, then back compute velocity from that
            tmp=xmomAll*(heightAll>minimum_allowed_height)
            htc = (heightAll[:,vols0] + heightAll[:,vols1] + heightAll[:,vols2])/3.0
            xmom=(tmp[:,vols0]+tmp[:,vols1]+tmp[:,vols2])/3.0
            xmom_cent=getInds(xmom,  timeSlices=inds, absMax=True)
            xvel_cent=getInds(xmom/(htc+1.0e-06), timeSlices=inds, absMax=True)

            tmp=ymomAll*(heightAll>minimum_allowed_height)
            ymom=(tmp[:,vols0]+tmp[:,vols1]+tmp[:,vols2])/3.0
            ymom_cent=getInds(ymom,  timeSlices=inds, absMax=True)
            yvel_cent=getInds(ymom/(htc+1.0e-06), timeSlices=inds, absMax=True)
            vel_cent = getInds( (xmom**2+ymom**2)**0.5/(htc+1.0e-06), timeSlices=inds)

    fid.close()
    
    return time, x_cent, y_cent, stage_cent, xmom_cent,\
             ymom_cent, height_cent, elev_cent, friction_cent,\
             xvel_cent, yvel_cent, vel_cent, xllcorner, yllcorner, inds


def animate_1D(time, var, x, ylab=' '): #, x=range(var.shape[1]), vmin=var.min(), vmax=var.max()):
    # Input: time = one-dimensional time vector;
    #        var =  array with first dimension = len(time) ;
    #        x = (optional) vector width dimension equal to var.shape[1];
    
    import pylab
    import numpy
   
    

    pylab.close()
    pylab.ion()

    # Initial plot
    vmin=var.min()
    vmax=var.max()
    line, = pylab.plot( (x.min(), x.max()), (vmin, vmax), 'o')

    # Lots of plots
    for i in range(len(time)):
        line.set_xdata(x)
        line.set_ydata(var[i,:])
        pylab.draw()
        pylab.xlabel('x')
        pylab.ylabel(ylab)
        pylab.title('time = ' + str(time[i]))
    
    return

def near_transect(p, point1, point2, tol=1.):
    # Function to get the indices of points in p less than 'tol' from the line
    # joining (x1,y1), and (x2,y2)
    # p comes from util.get_output('mysww.sww')
    #
    # e.g.
    # import util
    # from matplotlib import pyplot
    # p=util.get_output('merewether_1m.sww',0.01)
    # p2=util.get_centroids(p,velocity_extrapolation=True)
    # #xxx=transect_interpolate.near_transect(p,[95., 85.], [120.,68.],tol=2.)
    # xxx=util.near_transect(p,[95., 85.], [120.,68.],tol=2.)
    # pyplot.scatter(xxx[1],p.vel[140,xxx[0]],color='red')
    
    x1=point1[0]
    y1=point1[1]
    
    x2=point2[0]
    y2=point2[1]
    
    # Find line equation a*x + b*y + c = 0
    # based on y=gradient*x +intercept
    if x1!=x2:
        gradient= (y2-y1)/(x2-x1)
        intercept = y1 - gradient*x1
        #
        a = -gradient
        b = 1.
        c = -intercept
    else:
        a=1.
        b=0.
        c=-x2 
    
    # Distance formula
    inv_denom = 1./(a**2 + b**2)**0.5
    distp = abs(p.x*a + p.y*b + c)*inv_denom
    
    near_points = (distp<tol).nonzero()[0]
    
    # Now find a 'local' coordinate for the point, projected onto the line
    # g1 = unit vector parallel to the line
    # g2 = vector joining (x1,y1) and (p.x,p.y)
    g1x = x2-x1 
    g1y = y2-y1
    g1_norm = (g1x**2 + g1y**2)**0.5
    g1x=g1x/g1_norm
    g1y=g1y/g1_norm
    
    g2x = p.x[near_points] - x1
    g2y = p.y[near_points] - y1
    
    # Dot product = projected distance == a local coordinate
    local_coord = g1x*g2x + g1y*g2y
    
    # only keep coordinates between zero and the distance along the line
    dl=((x1-x2)**2+(y1-y2)**2)**0.5
    keepers=(local_coord<=dl)*(local_coord>=0.)
    keepers=keepers.nonzero()
    
    return near_points[keepers], local_coord[keepers]

########################
# TRIANGLE AREAS, WATER VOLUME
def triangle_areas(p, subset=None):
    # Compute areas of triangles in p -- assumes p contains vertex information
    # subset = vector of centroid indices to include in the computation. 

    if(subset is None):
        subset=range(len(p.vols[:,0]))
    
    x0=p.x[p.vols[subset,0]]
    x1=p.x[p.vols[subset,1]]
    x2=p.x[p.vols[subset,2]]
    
    y0=p.y[p.vols[subset,0]]
    y1=p.y[p.vols[subset,1]]
    y2=p.y[p.vols[subset,2]]
    
    # Vectors for cross-product
    v1_x=x0-x1
    v1_y=y0-y1
    #
    v2_x=x2-x1
    v2_y=y2-y1
    # Area
    area=(v1_x*v2_y-v1_y*v2_x)*0.5
    area=abs(area)
    return area

###

def water_volume(p, p2, per_unit_area=False, subset=None):
    # Compute the water volume from p(vertex values) and p2(centroid values)

    if(subset is None):
        subset=range(len(p2.x))

    l=len(p2.time)
    area=triangle_areas(p, subset=subset)
    
    total_area=area.sum()
    volume=p2.time*0.
   
    # This accounts for how volume is measured in ANUGA 
    # Compute in 2 steps to reduce precision error (important sometimes)
    # Is this really needed?
    for i in range(l):
        #volume[i]=((p2.stage[i,subset]-p2.elev[subset])*(p2.stage[i,subset]>p2.elev[subset])*area).sum()
        volume[i]=((p2.stage[i,subset])*(p2.stage[i,subset]>p2.elev[subset])*area).sum()
        volume[i]=volume[i]+((-p2.elev[subset])*(p2.stage[i,subset]>p2.elev[subset])*area).sum()
    
    if(per_unit_area):
        volume=volume/total_area 
    
    return volume


def get_triangle_containing_point(p,point):

    V = p.vols

    x = p.x
    y = p.y

    l = len(x)

    from anuga.geometry.polygon import is_outside_polygon,is_inside_polygon

    # FIXME: Horrible brute force
    for i in xrange(l):
        i0 = V[i,0]
        i1 = V[i,1]
        i2 = V[i,2]
        poly = [ [x[i0], y[i0]], [x[i1], y[i1]], [x[i2], y[i2]] ]

        if is_inside_polygon(point, poly, closed=True):
            return i

    msg = 'Point %s not found within a triangle' %str(point)
    raise Exception(msg)


def get_extent(p):

    import numpy

    x_min = numpy.min(p.x)
    x_max = numpy.max(p.x)

    y_min = numpy.min(p.y)
    y_max = numpy.max(p.y)

    return x_min, x_max, y_min, y_max



def make_grid(data, lats, lons, fileName, EPSG_CODE=None, proj4string=None):
    """
        Convert data,lats,lons to a georeferenced raster tif
        INPUT: data -- array with desired raster cell values
               lats -- 1d array with 'latitude' or 'y' range
               lons -- 1D array with 'longitude' or 'x' range
               fileName -- name of file to write to
               EPSG_CODE -- Integer code with projection information in EPSG format 
               proj4string -- proj4string with projection information

        NOTE: proj4string is used in preference to EPSG_CODE if available
    """
    try:
        import gdal
        import osr
    except:
        raise Exception, 'Cannot find gdal and/or osr python modules'

    xres = lons[1] - lons[0]
    yres = lats[1] - lats[0]

    ysize = len(lats)
    xsize = len(lons)

    # Assume data/lats/longs refer to cell centres, and compute upper left coordinate
    ulx = lons[0] - (xres / 2.)
    uly = lats[lats.shape[0]-1] + (yres / 2.)

    # GDAL magic to make the tif
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(fileName, xsize, ysize, 1, gdal.GDT_Float32)

    srs = osr.SpatialReference()
    if(proj4string is not None):
        srs.ImportFromProj4(proj4string)
    elif(EPSG_CODE is not None):
        srs.ImportFromEPSG(EPSG_CODE)
    else:
        raise Exception, 'No spatial reference information given'

    ds.SetProjection(srs.ExportToWkt())

    gt = [ulx, xres, 0, uly, 0, -yres ]
    #gt = [llx, xres, 0, lly, yres,0 ]
    ds.SetGeoTransform(gt)

    #import pdb
    #pdb.set_trace()

    outband = ds.GetRasterBand(1)
    outband.WriteArray(data)

    ds = None
    return

##################################################################################

def Make_Geotif(swwFile=None, 
             output_quantities=['depth'],
             myTimeStep=0, CellSize=5.0, 
             lower_left=None, upper_right=None,
             EPSG_CODE=None, 
             proj4string=None,
             velocity_extrapolation=True,
             min_allowed_height=1.0e-05,
             output_dir='TIFS',
             bounding_polygon=None,
             verbose=False):
    """
        Make a georeferenced tif by nearest-neighbour interpolation of sww file outputs (or a 3-column array with xyz Points)

        You must supply projection information as either a proj4string or an integer EPSG_CODE (but not both!)

        INPUTS: swwFile -- name of sww file, OR a 3-column array with x/y/z
                    points. In the latter case x and y are assumed to be in georeferenced
                    coordinates.  The output raster will contain 'z', and will have a name-tag
                    based on the name in 'output_quantities'.
                output_quantities -- list of quantitiies to plot, e.g.
                                ['depth', 'velocity', 'stage','elevation','depthIntegratedVelocity','friction']
                myTimeStep -- list containing time-index of swwFile to plot (e.g. [0, 10, 32] ) or 'last', or 'max', or 'all'
                CellSize -- approximate pixel size for output raster [adapted to fit lower_left / upper_right]
                lower_left -- [x0,y0] of lower left corner. If None, use extent of swwFile.
                upper_right -- [x1,y1] of upper right corner. If None, use extent of swwFile.
                EPSG_CODE -- Projection information as an integer EPSG code (e.g. 3123 for PRS92 Zone 3, 32756 for UTM Zone 56 S, etc). 
                             Google for info on EPSG Codes
                proj4string -- Projection information as a proj4string (e.g. '+init=epsg:3123')
                             Google for info on proj4strings. 
                velocity_extrapolation -- Compute velocity assuming the code extrapolates with velocity (instead of momentum)?
                min_allowed_height -- Minimum allowed height from ANUGA
                output_dir -- Write outputs to this directory
                bounding_polygon -- polygon (e.g. from read_polygon) If present, only set values of raster cells inside the bounding_polygon
                
    """

    #import pdb
    #pdb.set_trace()

    try:
        import gdal
        import osr
        import scipy.io
        import scipy.interpolate
        import anuga
        from anuga.utilities import plot_utils as util
        import os
        from matplotlib import nxutils
    except:
        raise Exception, 'Required modules not installed for Make_Geotif'


    # Check whether swwFile is an array, and if so, redefine various inputs to
    # make the code work
    if(type(swwFile)==scipy.ndarray):
        import copy
        xyzPoints=copy.copy(swwFile)
        swwFile=None

    if(((EPSG_CODE is None) & (proj4string is None) )|
       ((EPSG_CODE is not None) & (proj4string is not None))):
        raise Exception, 'Must specify EITHER an integer EPSG_CODE describing the file projection, OR a proj4string'


    # Make output_dir
    try:
        os.mkdir(output_dir)
    except:
        pass

    if(swwFile is not None):
        # Read in ANUGA outputs
        
        # Ensure myTimeStep is a list
        if type(myTimeStep)!=list:
            myTimeStep=[myTimeStep]
            
        if(verbose):
            print 'Reading sww File ...'
        p2=util.get_centroids(swwFile, velocity_extrapolation, timeSlices=myTimeStep,
                              minimum_allowed_height=min_allowed_height)
        xllcorner=p2.xllcorner
        yllcorner=p2.yllcorner

        #if(myTimeStep=='all'):
        #    myTimeStep=range(len(p2.time))
        #elif(myTimeStep=='last'):
        #    # This is [0]!
        #    myTimeStep=[len(p2.time)-1]

        # Now, myTimeStep just holds indices we want to plot in p2
        if(myTimeStep!='max'):
            myTimeStep=range(len(p2.time))


        if(verbose):
            print 'Extracting required data ...'
        # Get ANUGA points
        swwX=p2.x+xllcorner
        swwY=p2.y+yllcorner
    else:
        # Get the point data from the 3-column array
        if(xyzPoints.shape[1]!=3):
            raise Exception, 'If an array is passed, it must have exactly 3 columns'
        if(len(output_quantities)!=1):
            raise Exception, 'Can only have 1 output quantity when passing an array'
        swwX=xyzPoints[:,0]
        swwY=xyzPoints[:,1]
        myTimeStep=['pointData']

    # Grid for meshing
    if(verbose):
        print 'Computing grid of output locations...'
    # Get points where we want raster cells
    if(lower_left is None):
        lower_left=[swwX.min(),swwY.min()]
    if(upper_right is None):
        upper_right=[swwX.max(),swwY.max()]
    nx=round((upper_right[0]-lower_left[0])*1.0/(1.0*CellSize)) + 1
    xres=(upper_right[0]-lower_left[0])*1.0/(1.0*(nx-1))
    desiredX=scipy.arange(lower_left[0], upper_right[0],xres )
    ny=round((upper_right[1]-lower_left[1])*1.0/(1.0*CellSize)) + 1
    yres=(upper_right[1]-lower_left[1])*1.0/(1.0*(ny-1))
    desiredY=scipy.arange(lower_left[1], upper_right[1], yres)

    gridX, gridY=scipy.meshgrid(desiredX,desiredY)

    if(verbose):
        print 'Making interpolation functions...'
    swwXY=scipy.array([swwX[:],swwY[:]]).transpose()
    # Get index of nearest point
    index_qFun=scipy.interpolate.NearestNDInterpolator(swwXY,scipy.arange(len(swwX),dtype='int64').transpose())
    gridXY_array=scipy.array([scipy.concatenate(gridX),scipy.concatenate(gridY)]).transpose()
    gridqInd=index_qFun(gridXY_array)

    if(bounding_polygon is not None):
        # Find points to exclude (i.e. outside the bounding polygon)
        cut_points=(nxutils.points_inside_poly(gridXY_array, bounding_polygon)==False).nonzero()[0]
       
    # Loop over all output quantities and produce the output
    for myTSi in myTimeStep:
        if(verbose):
            print myTSi
        for output_quantity in output_quantities:
            if (verbose): print output_quantity

            if(myTSi is not 'max'):
                myTS=myTSi
            else:
                # We have already extracted the max, and e.g.
                # p2.stage is an array of dimension (1, number_of_pointS).
                myTS=0

            if(type(myTS)==int):
                if(output_quantity=='stage'):
                    gridq=p2.stage[myTS,:][gridqInd]
                if(output_quantity=='depth'):
                    gridq=p2.height[myTS,:][gridqInd]
                    gridq=gridq*(gridq>=0.) # Force positive depth (tsunami alg)
                if(output_quantity=='velocity'):
                    gridq=p2.vel[myTS,:][gridqInd]
                if(output_quantity=='friction'):
                    gridq=p2.friction[gridqInd]
                if(output_quantity=='depthIntegratedVelocity'):
                    swwDIVel=(p2.xmom[myTS,:]**2+p2.ymom[myTS,:]**2)**0.5
                    gridq=swwDIVel[gridqInd]
                if(output_quantity=='elevation'):
                    gridq=p2.elev[gridqInd]
    
                if(myTSi is 'max'):
                    timestepString='max'
                else:
                    timestepString=str(round(p2.time[myTS]))
            elif(myTS=='pointData'):
                gridq=xyzPoints[:,2][gridqInd]


            if(bounding_polygon is not None):
                # Cut the points outside the bounding polygon
                gridq[cut_points]=scipy.nan 

            # Make name for output file
            if(myTS!='pointData'):
                output_name=output_dir+'/'+os.path.splitext(os.path.basename(swwFile))[0] + '_'+\
                            output_quantity+'_'+timestepString+\
                            '.tif'
                            #'_'+str(myTS)+'.tif'
            else:
                output_name=output_dir+'/'+'PointData_'+output_quantity+'.tif'

            if(verbose):
                print 'Making raster ...'
            gridq.shape=(len(desiredY),len(desiredX))
            make_grid(scipy.flipud(gridq),desiredY,desiredX, output_name,EPSG_CODE=EPSG_CODE, proj4string=proj4string)

    return

def plot_triangles(p, adjustLowerLeft=False):
    """ Add mesh triangles to a pyplot plot
    """
    from matplotlib import pyplot as pyplot
    #
    x0=p.xllcorner
    x1=p.yllcorner 
    #
    for i in range(len(p.vols)):
        k1=p.vols[i][0]
        k2=p.vols[i][1]
        k3=p.vols[i][2]
        if(not adjustLowerLeft):
            pyplot.plot([p.x[k1], p.x[k2], p.x[k3], p.x[k1]], [p.y[k1], p.y[k2], p.y[k3], p.y[k1]],'-',color='black')
        else:
            pyplot.plot([p.x[k1]+x0, p.x[k2]+x0, p.x[k3]+x0, p.x[k1]+x0], [p.y[k1]+x1, p.y[k2]+x1, p.y[k3]+x1, p.y[k1]+x1],'-',color='black')
        #pyplot.plot([p.x[k3], p.x[k2]], [p.y[k3], p.y[k2]],'-',color='black')
        #pyplot.plot([p.x[k3], p.x[k1]], [p.y[k3], p.y[k1]],'-',color='black')

def find_neighbours(p,ind):
    """ 
        Find the triangles neighbouring triangle 'ind'
        p is an object from get_output containing mesh vertices
    """
    ind_nei=p.vols[ind]
    
    shared_nei0=p.vols[:,1]*0.0
    shared_nei1=p.vols[:,1]*0.0
    shared_nei2=p.vols[:,1]*0.0
    # Compute indices that match one of the vertices of triangle ind
    # Note: Each triangle can only match a vertex, at most, once
    for i in range(3):
        shared_nei0+=1*(p.x[p.vols[:,i]]==p.x[ind_nei[0]])*\
            1*(p.y[p.vols[:,i]]==p.y[ind_nei[0]])
        
        shared_nei1+=1*(p.x[p.vols[:,i]]==p.x[ind_nei[1]])*\
            1*(p.y[p.vols[:,i]]==p.y[ind_nei[1]])
        
        shared_nei2+=1*(p.x[p.vols[:,i]]==p.x[ind_nei[2]])*\
            1*(p.y[p.vols[:,i]]==p.y[ind_nei[2]])
    
    out=(shared_nei2 + shared_nei1 + shared_nei0)
    return((out==2).nonzero())

def calc_edge_elevations(p):
    """
        Compute the triangle edge elevations on p
        Return x,y,elev for edges
    """
    pe_x=p.x*0.
    pe_y=p.y*0.
    pe_el=p.elev*0.

   
    # Compute coordinates + elevations 
    pe_x[p.vols[:,0]] = 0.5*(p.x[p.vols[:,1]] + p.x[p.vols[:,2]])
    pe_y[p.vols[:,0]] = 0.5*(p.y[p.vols[:,1]] + p.y[p.vols[:,2]])
    pe_el[p.vols[:,0]] = 0.5*(p.elev[p.vols[:,1]] + p.elev[p.vols[:,2]])
    
    pe_x[p.vols[:,1]] = 0.5*(p.x[p.vols[:,0]] + p.x[p.vols[:,2]])
    pe_y[p.vols[:,1]] = 0.5*(p.y[p.vols[:,0]] + p.y[p.vols[:,2]])
    pe_el[p.vols[:,1]] = 0.5*(p.elev[p.vols[:,0]] + p.elev[p.vols[:,2]])

    pe_x[p.vols[:,2]] = 0.5*(p.x[p.vols[:,0]] + p.x[p.vols[:,1]])
    pe_y[p.vols[:,2]] = 0.5*(p.y[p.vols[:,0]] + p.y[p.vols[:,1]])
    pe_el[p.vols[:,2]] = 0.5*(p.elev[p.vols[:,0]] + p.elev[p.vols[:,1]])

    return [pe_x, pe_y, pe_el]


