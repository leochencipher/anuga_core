#!/usr/bin/env python
#

import unittest
import tempfile
import os
import time
import csv

#from anuga.damage.inundation_damage import _calc_collapse_structures
from inundation_damage import *
from anuga.geospatial_data.geospatial_data import Geospatial_data
from anuga.pmesh.mesh import Mesh
from anuga.coordinate_transforms.geo_reference import Geo_reference
from anuga.shallow_water import Domain, Transmissive_boundary
from anuga.utilities.numerical_tools import mean
from anuga.shallow_water.data_manager import get_dataobject

from Numeric import zeros, Float, allclose


def elevation_function(x, y):
    return -x

class Test_inundation_damage(unittest.TestCase):
    def setUp(self):
        #print "****set up****"
        # Create an sww file
        
        # Set up an sww that has a geo ref.
        # have it cover an area in Australia.  'gong maybe
        #Don't have many triangles though!
        
        #Site Name:    GDA-MGA: (UTM with GRS80 ellipsoid) 
        #Zone:   56    
        #Easting:  222908.705  Northing: 6233785.284 
        #Latitude:   -34  0 ' 0.00000 ''  Longitude: 150  0 ' 0.00000 '' 
        #Grid Convergence:  -1  40 ' 43.13 ''  Point Scale: 1.00054660

        #geo-ref
        #Zone:   56    
        #Easting:  220000  Northing: 6230000 


        #have  a big area covered.

        mesh_file = tempfile.mktemp(".tsh")
        
        points_lat_long = [[-33,152],[-35,152],[-35,150],[-33,150]]
       
        spat = Geospatial_data(data_points=points_lat_long,
                               points_are_lats_longs=True)
        points_ab = spat.get_data_points( absolute = True)

        
        geo =  Geo_reference(56,400000,6000000)
        spat.set_geo_reference(geo)

        m = Mesh()
        m.add_vertices(spat)
        m.auto_segment()
        m.generate_mesh(verbose=False)
        m.export_mesh_file(mesh_file)

        
        #Create shallow water domain
        domain = Domain(mesh_file)

        os.remove(mesh_file)
        
        domain.default_order=2
        domain.beta_h = 0


        #Set some field values
        #domain.set_quantity('stage', 1.0)
        domain.set_quantity('elevation', -0.5)
        domain.set_quantity('friction', 0.03)


        ######################
        # Boundary conditions
        B = Transmissive_boundary(domain)
        domain.set_boundary( {'exterior': B})


        ######################
        #Initial condition - with jumps

        bed = domain.quantities['elevation'].vertex_values
        stage = zeros(bed.shape, Float)

        h = 0.3
        for i in range(stage.shape[0]):
            if i % 2 == 0:
                stage[i,:] = bed[i,:] + h
            else:
                stage[i,:] = bed[i,:]

        domain.set_quantity('stage', stage)
        domain.set_quantity('xmomentum', stage*22.0)
        domain.set_quantity('ymomentum', stage*55.0)

        domain.distribute_to_vertices_and_edges()


        self.domain = domain

        C = domain.get_vertex_coordinates()
        self.X = C[:,0:6:2].copy()
        self.Y = C[:,1:6:2].copy()

        self.F = bed

        
        #sww_file = tempfile.mktemp("")
        self.domain.filename = 'datatest' + str(time.time())
        #self.domain.filename = sww_file
        #print "self.domain.filename",self.domain.filename 
        self.domain.format = 'sww'
        self.domain.smooth = True
        self.domain.reduction = mean

        sww = get_dataobject(self.domain)
        sww.store_connectivity()
        sww.store_timestep(['stage', 'xmomentum', 'ymomentum'])
        self.domain.time = 2.
        sww.store_timestep(['stage', 'xmomentum', 'ymomentum'])
        self.sww = sww # so it can be deleted
        
        #Create a csv file
        self.csv_file = tempfile.mktemp(".csv")
        fd = open(self.csv_file,'wb')
        writer = csv.writer(fd)
        writer.writerow(['LONGITUDE','LATITUDE','STR_VALUE','C_VALUE','ROOF_TYPE','WALLS', 'SHORE_DIST'])
        writer.writerow(['151.5','-34','199770','130000','Metal','Timber',20.])
        writer.writerow(['151','-34.5','150000','76000','Metal','Double Brick',200.])
        writer.writerow(['151','-34.25','150000','76000','Metal','Brick Veneer',200.])
        fd.close()

        
    def tearDown(self):
        #print "***** tearDown  ********"

        # FIXME (Ole): Sometimes this fails - is the file open or is it sometimes not created?
        os.remove(self.sww.filename)
        os.remove(self.csv_file)

    
    def test_inundation_damage(self):

        # Note, this isn't testing the results,
        # just that is all runs
        sww_file = self.domain.filename + "." + self.domain.format
        #print "sww_file",sww_file 
        inundation_damage(sww_file, self.csv_file, verbose=False)

    
    def test_inundation_damage2(self):

        # create mesh
        mesh_file = tempfile.mktemp(".tsh")    
        points = [[0.0,0.0],[6.0,0.0],[6.0,6.0],[0.0,6.0]]
        m = Mesh()
        m.add_vertices(points)
        m.auto_segment()
        m.generate_mesh(verbose=False)
        m.export_mesh_file(mesh_file)
        
        #Create shallow water domain
        domain = Domain(mesh_file)
        os.remove(mesh_file)
        
        domain.default_order=2
        domain.beta_h = 0

        #Set some field values
        domain.set_quantity('elevation', elevation_function)
        domain.set_quantity('friction', 0.03)
        domain.set_quantity('xmomentum', 22.0)
        domain.set_quantity('ymomentum', 55.0)

        ######################
        # Boundary conditions
        B = Transmissive_boundary(domain)
        domain.set_boundary( {'exterior': B})

        # This call mangles the stage values.
        domain.distribute_to_vertices_and_edges()
        domain.set_quantity('stage', 0.3)

        #sww_file = tempfile.mktemp("")
        domain.filename = 'datatest' + str(time.time())
        #domain.filename = sww_file
        #print "domain.filename",domain.filename 
        domain.format = 'sww'
        domain.smooth = True
        domain.reduction = mean

        sww = get_dataobject(domain)
        sww.store_connectivity()
        sww.store_timestep(['stage', 'xmomentum', 'ymomentum'])
        domain.set_quantity('stage', -0.3)
        domain.time = 2.
        sww.store_timestep(['stage', 'xmomentum', 'ymomentum'])
        
        #Create a csv file
        csv_file = tempfile.mktemp(".csv")
        fd = open(csv_file,'wb')
        writer = csv.writer(fd)
        writer.writerow(['x','y','STR_VALUE','C_VALUE','ROOF_TYPE','WALLS', 'SHORE_DIST'])
        writer.writerow([5.5,0.5,'10','130000','Metal','Timber',20])
        writer.writerow([4.5,1.0,'150','76000','Metal','Double Brick',20])
        writer.writerow([0.1,1.5,'100','76000','Metal','Brick Veneer',300])
        writer.writerow([6.1,1.5,'100','76000','Metal','Brick Veneer',300])
        fd.close()

        sww_file = domain.filename + "." + domain.format
        #print "sww_file",sww_file 
        inundation_damage(sww_file, csv_file, verbose=False)

        csv_handle = Exposure_csv(csv_file)
        struct_loss = csv_handle.get_column(EventDamageModel.STRUCT_LOSS_TITLE)
        #print "struct_loss",struct_loss
        struct_loss = [float(x) for x in struct_loss]
        assert allclose(struct_loss,[10,150,16.9,0])
        depth = csv_handle.get_column(EventDamageModel.MAX_DEPTH_TITLE)
        #print "depth",depth
        depth = [float(x) for x in depth]
        assert allclose(depth,[5.5,4.5,0.1,-0.3])
        os.remove(sww.filename)
        os.remove(csv_file)
        
    def ztest_add_depth_and_momentum2csv(self):
        sww_file = self.domain.filename + "." + self.domain.format
        #print "sww_file",sww_file
        
        out_csv = tempfile.mktemp(".csv")
        print "out_csv",out_csv 
        add_depth_and_momentum2csv(sww_file, self.csv_file,
                                   out_csv, verbose=False)
        
    def test_calc_damage_percentages(self):
        max_depths = [-0.3, 0.0, 1.0,-0.3, 0.0, 1.0,-0.3, 0.0, 1.0]
        shore_distances = [100, 100, 100, 100, 100, 100, 100, 100, 100]
        walls = ['Double Brick',
                 'Double Brick',
                 'Double Brick',
                 'Timber',
                 'Timber',
                 'Timber',
                 'Brick Veneer',
                 'Brick Veneer',
                 'Brick Veneer']
        struct_costs = [10,
                        10,
                        10,
                        10,
                        10,
                        10,
                        1,
                        1,
                        1]
        content_costs = [100,
                        100,
                        100,
                        100,
                        100,
                        100,
                        10,
                        10,
                        10]

        edm = EventDamageModel(max_depths, shore_distances, walls,
                               struct_costs, content_costs)
        edm.calc_damage_percentages()
        assert allclose(edm.struct_damage,[0.0,0.016,0.572,
                                            0.0,0.016,0.618,
                                            0.0,0.016,0.618])
        assert allclose(edm.contents_damage,[0.0,0.013,0.970,
                                             0.0,0.013,0.970,
                                             0.0,0.013,0.970])
        edm.calc_cost()
        assert allclose(edm.struct_loss,[0.0,.16,5.72,
                                            0.0,.16,6.18,
                                            0.0,0.016,0.618])
        assert allclose(edm.contents_loss,[0.0,1.3,97,
                                             0.0,1.3,97,
                                             0.0,0.13,9.7])
        
        
    def test_calc_collapse_structures(self):
        edm = EventDamageModel([0.0]*17, [0.0]*17, [0.0]*17,
                               [0.0]*17, [0.0]*17)
        edm.struct_damage = zeros(17,Float) 
        edm.contents_damage = zeros(17,Float) 
        collapse_probability = {0.4:[0], #0
                                0.6:[1], #1
                                0.5:[2], #1
                                0.25:[3,4], #1
                                0.1:[5,6,7,8], #0
                                0.2:[9,10,11,12,13,14,15,16]} #2
        edm._calc_collapse_structures(collapse_probability, verbose_csv=True)

        self.failUnless( edm.struct_damage[0]  == 0.0 and
                         edm.contents_damage[0]  == 0.0,
                        'Error!')
        self.failUnless( edm.struct_damage[1]  == 1.0 and
                         edm.contents_damage[1]  == 1.0,
                        'Error!')
        self.failUnless( edm.struct_damage[2]  == 1.0 and
                         edm.contents_damage[2]  == 1.0,
                        'Error!')
        self.failUnless( edm.struct_damage[3]+ edm.struct_damage[4] == 1.0 and
                         edm.contents_damage[3] + edm.contents_damage[4] ==1.0,
                        'Error!')
        sum_struct = 0.0
        sum_contents = 0.0
        for i in [5,6,7,8]:
            sum_struct += edm.struct_damage[i]
            sum_contents += edm.contents_damage[i]
        print "", 
        self.failUnless( sum_struct == 0.0 and sum_contents  == 0.0,
                        'Error!')
        sum_struct = 0.0
        sum_contents = 0.0
        for i in [9,10,11,12,13,14,15,16]:
            sum_struct += edm.struct_damage[i]
            sum_contents += edm.contents_damage[i]
        self.failUnless( sum_struct == 2.0 and sum_contents  == 2.0,
                        'Error!')
        
    def test_calc_collapse_probability(self):
        depth =          [0.0, 0.5, 0.5  , 1.5, 2.5, 4.5, 10000, 2.0]
        shore_distance = [0.0, 125, 250.1, 0.0, 150, 225, 10000, 251]
        dummy = depth
        edm = EventDamageModel(depth, shore_distance, dummy, dummy, dummy)
        struct_coll_prob = edm.calc_collapse_probability()
        answer = {0.05:[1,7],
                  0.6:[3],
                  0.4:[4],
                  0.5:[5],
                  0.45:[6]}
        #print "struct_coll_prob",struct_coll_prob 
        #print "answer",answer 

        self.failUnless( struct_coll_prob ==  answer,
                        'Error!')
        
        
    def test_calc_damage_and_costs(self):
                             
        max_depths = [-0.3, 0.0, 1.0,-0.3, 0.0, 1.0,-0.3, 0.0, 10.0]
        shore_distances = [100, 100, 100, 100, 100, 100, 100, 100, 100]
        walls = ['Double Brick',
                 'Double Brick',
                 'Double Brick',
                 'Timber',
                 'Timber',
                 'Timber',
                 'Brick Veneer',
                 'Brick Veneer',
                 'Brick Veneer']
        struct_costs = [10,
                        10,
                        10,
                        10,
                        10,
                        10,
                        1,
                        1,
                        1]
        content_costs = [100,
                        100,
                        100,
                        100,
                        100,
                        100,
                        10,
                        10,
                        10]

        edm = EventDamageModel(max_depths, shore_distances, walls,
                               struct_costs, content_costs)
        results_dic = edm.calc_damage_and_costs(verbose_csv=True)
        #print "results_dic",results_dic
#-------------------------------------------------------------
if __name__ == "__main__":
    #suite = unittest.makeSuite(Test_inundation_damage,'test_in_damage2')
    suite = unittest.makeSuite(Test_inundation_damage,'test')
    runner = unittest.TextTestRunner()
    runner.run(suite)

