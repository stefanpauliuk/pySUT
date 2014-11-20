# -*- coding: utf-8 -*-
"""
Functions and classes for efficient handling of supply and use tables (SUTs)

Created on Mon Jun 30 17:21:28 2014

@author: stefan pauliuk, NTNU Trondheim, Norway

standard abbreviation: SUT

dependencies:
    numpy
    scipy

How to load this class:
- add class folder to system path
sys.path.append(Package_Path)

import pySUT
imp.reload(pySUT)
from pySUT import SUT    
    
"""

# import os
import sys
import IPython
import logging
# import string
import numpy as np
# pylint: disable-msg=C0103

# import pandas as pd
# import scipy.sparse.linalg as slinalg
# import scipy.sparse as sparse

# check for correct version number
if sys.version_info.major < 3: 
    logging.warning('This package requires Python 3.0 or higher.')

class SUT(object):
    """ Class containing a complete supply and use table

    Attributes
    ----------
    V : product by industry supply table
    U : product by industry use table
    Y : final demand product by end-use category
    F : Extensions: type by industry
    FY: Extensions: type by end-use category
    TL: Trade link (for MRIO models)        
    
        
    unit : Unit for each row of V,U, and y (product unit)
    version : string
        This can be used as a version tracking system. 
    year : string or int
        Baseyear of the IOSystem
    name : string, optional
        Name of the SUT, default is 'SUT'

    E_bar : Mapping of primary production
            + product-by-industry matrix of integers
            + coefficient 1 to indicate primary product and 0 otherwise

   
    """
    
    """
    Basic initialisation and dimension check methods
    """    

    def __init__(self, V=None, U=None, Y=None, F=None, FY=None, TL=None,
            unit=None, version=None, year=None, name='SUT',
            regions=1, E_bar=None, Xi=None, PSI=None, PHI=None, Gamma=None):
        """ Init function """
        self.V = V # mandatory
        self.U = U # mandatory
        self.Y = Y # optional
        self.F = F # optional
        self.FY= FY# optional
        self.TL= TL# optional
       
        self.name = name  # optional
        self.regions = regions # Number of regions, for multiregional SUT
        self.unit = unit  # optional       
        self.year = year  # optional
        self.version = version  # optional

        self.E_bar = E_bar # optional
        self.Xi = Xi
        self.PSI = PSI
        self.PHI = PHI
        self.Gamma = Gamma
        
    def return_version_info(self):
        return str('Class SUT. Version 0.1. Last change: September 24th, 2014.')            
        
    def dimension_check(self):
        """ This method checks which variables are present and checks whether data types and dimensions match
        """
        # Compile a little report on the presence and dimensions of the elements in the SUT
        DimReport  = str('<br><b> Checking dimensions of SUT structure</b><br>')
        if self.V != None:
            DimReport += str('Supply table is present with ' + str(len(self.V)) + ' rows (products) and ' + str(len(self.V[0])) + ' columns (industries).<br>')                        
        else:
            DimReport += str('Supply table is not present.<br>')                        
        if self.U != None:
            DimReport += str('Use table is present with ' + str(len(self.U)) + ' rows (products) and ' + str(len(self.U[0])) + ' columns (industries).<br>')                        
        else:
            DimReport += str('Use table is not present.<br>')                        
        if self.Y != None:
            if len(self.Y.shape) == 1: # if Y is a true vector
                DimReport += str('Final demand is present with ' + str(len(self.Y)) + ' rows (products) and 1 column (FD categories).<br>')                        
            else:
                DimReport += str('Final demand is present with ' + str(len(self.Y)) + ' rows (products) and ' + str(len(self.Y[0])) + ' columns (FD categories).<br>')                        
        else:
            DimReport += str('Final demand is not present.<br>')                                    
        if self.F != None:
            DimReport += str('Industry extensions are present with ' + str(len(self.F)) + ' rows (stressors) and ' + str(len(self.F[0])) + ' columns (industries).<br>')                        
        else:
            DimReport += str('Industry extensions are not present.<br>')     
        if self.FY != None:
            DimReport += str('FD extensions are present with ' + str(len(self.FY)) + ' rows (stressors) and ' + str(len(self.FY[0])) + ' columns (FD categories).<br>')                        
        else:
            DimReport += str('FD extensions are not present.<br>')  
        if self.TL != None:
            DimReport += str('Trade link is present with ' + str(len(self.TL)) + ' rows (products) and ' + str(len(self.TL[0])) + ' columns (regions).<br>')                        
        else:
            DimReport += str('Trade link is not present.<br>')              

        # for most operations, especially the constructs, U and V are required to be present and have correct dimensions. We check for this:
        if self.U != None:
            if self.V != None:
                if len(self.V) == len(self.U):
                    if len(self.V[0]) == len(self.U[0]):
                        StatusFlag = 1 # V and U have proper dimensions
                    else: 
                        StatusFlag = 0
                else: 
                    StatusFlag = 0
            else: 
                StatusFlag = 0
        else: 
            StatusFlag = 0
        
        return DimReport, StatusFlag
        
    def compare_IndustrialUseAndSupply(self):
        """ This method computes total industrial supply and total industrial use, and compares the two
        ResultVector = U.e */ V.e
        """
        return self.U.sum(axis=1) / self.V.sum(axis=1)   
        
    def supply_diag_check(self): 
        """ to apply the BTC, we need to have a non-zero diagonal for each producing sector.
        Determine which sectors produce: """
        SupplySum_i = self.g_V()
        SupplySum_p = self.q_V()
        SupplyDiag  = self.V.diagonal()
        SupplyDiag_Eval = np.zeros((self.V.shape[0],7))
        for m in range(0,self.V.shape[0]):
            if SupplySum_p[m] != 0:
                if SupplySum_i[m] != 0:
                    if SupplyDiag[m] != 0:
                        SupplyDiag_Eval[m,0] = 1 # Normal situation, OK
                    else:
                        SupplyDiag_Eval[m,1] = 1 # No supply by apparent main producer, problem
                else:
                    SupplyDiag_Eval[m,2] = 1 # Product only produced by other sectors, this sector is empty
            else:
                if SupplySum_i[m] != 0:
                    SupplyDiag_Eval[m,3] = 1 # product not produced, apparent main sector produces only other products
                else:
                    SupplyDiag_Eval[m,4] = 1 # Product not produced and main sector is empty
            SupplyDiag_Eval[m,5] = SupplySum_p[m]
            SupplyDiag_Eval[m,6] = SupplySum_i[m]
                            
        return SupplyDiag_Eval        
        
    """
    Basic computations, row sum, col sum, etc.
    """            

    def g_V(self):
        """ Compute total industrial output g from supply table V."""
        return self.V.sum(axis=0)

    def q_V(self):
        """ Compute total product output g from supply table V."""
        return self.V.sum(axis=1)       
        
    def return_diag_V(self):
        """ Returns the diagonal of the supply table in matrix form : V^              """
        if self.V.shape[0] != self.V.shape[1]:
            raise ValueError('Error: Supply table is not square, there is no proper diagonal of that matrix.')
        else:
            Result_Array = np.zeros((self.V.shape[0],self.V.shape[0]))
            for m in range(0,self.V.shape[0]):
                Result_Array[m,m] = self.V[m,m]
            return Result_Array
            
    def return_offdiag_V(self):
        """   Returns the off-diagonal of the supply table in matrix form : V_offdiag              """
        if self.V.shape[0] != self.V.shape[1]:
            raise ValueError('Error: Supply table is not square, there is no proper diagonal of that matrix.')
        else:
            Result_Array = self.V.copy()
            for m in range(0,self.V.shape[0]):
                Result_Array[m,m] = 0
            return Result_Array    
            
    def market_balance(self):
        """ Returns the market balance of the SUT."""            
        if self.Y != None:
            if len(self.Y.shape) == 1: # if Y is a true vector
                return self.V.sum(axis=1) - self.U.sum(axis=1) - self.Y
            else: # if Y is an array
                return self.V.sum(axis=1) - self.U.sum(axis=1) - self.Y.sum(axis=1)
        else:
           raise ValueError('Error: There is no final demand; the market balance cannot be computed.') 
       
    """
    Aggregation, removal, and re-arrangement methods
    """  
        
    def aggregate_rearrange_products(self, PA, PR):
        """ multiplies an aggregation matrix PA from the left to V, U, and Y, rearranges the rows in columns of V, U, and Y according to the sorting matrix PR
        Equations: X_aggregated = PA * X, where X = U, V, or Y (and also TL)
        X_new = PR * X_aggregated * PR', where X = U, V 
        Y_new = PR * Y_aggregated (and also TL)
        """
        self.V  = np.dot(PR,np.dot(np.dot(PA,self.V),PR.transpose()))
        self.U  = np.dot(PR,np.dot(np.dot(PA,self.U),PR.transpose()))
        if self.Y != None:        
            self.Y  = np.dot(PR,np.dot(PA,self.Y))
        if self.F != None:
            self.F  = np.dot(self.F,PR.transpose())
        # No changes apply to FY
        if self.TL != None:
            self.TL  = np.dot(PR,np.dot(PA,self.TL))

        return 'Products were aggregated. Products and industries were resorted successfully.'       


    def _aggregate_regions_vectorised(self, X,  AV=None, axis=None):

        if AV is None:
            AV = np.ones(self.regions, dtype=int)

        # Use local variables for this method
        # Generate region correspondence matrix for aggregation
        pos = np.zeros((len(AV), max(AV)), dtype=int)
        pos[np.arange(len(AV)), AV - 1 ] = 1

        if axis == 0 or axis is None:
            # Generate aggregation matrix
            entries_per_region = int(X.shape[0]/len(AV))
            agg = np.kron(pos, np.eye(entries_per_region, dtype=int))

            # Aggregate rows
            X = agg.T.dot(X)

        if axis == 1 or axis is None:
            # Generate aggregation matrix
            entries_per_region = int(X.shape[1]/len(AV))
            agg = np.kron(pos, np.eye(entries_per_region, dtype=int))

            # Aggregate columns
            X = X.dot(agg)

        return X

    def aggregate_within_regions(self, X, axis=None):
        """ Aggregate the products or industries within each regions for mrSUT

        For multi-regional SUT, aggregate rows, columns or both such that
        there remains only one entry per region along chosen axis. The number
        of regions is specified by self.regions.

        Args
        ----
            X: a numpy array of appropriate dimensions
            axis: 0 to aggregate rows, 1 for columns, None for all.
                  + default: None
        Returns
        -------
            X

        """
        if axis == 0 or axis is None:
            # Generate aggregation matrix
            entries_per_regions = int(X.shape[0] / self.regions)
            e = np.ones((entries_per_regions, 1))
            agg = np.kron(np.eye(self.regions), e)

            # Aggregate rows to one entry per region
            X = agg.T.dot(X)

        if axis == 1 or axis is None:
            # Generate aggregation matrix
            entries_per_regions = int(X.shape[1] / self.regions)
            e = np.ones((entries_per_regions, 1))
            agg = np.kron(np.eye(self.regions), e)

            # Aggregate columns to one entry per region
            X = X.dot(agg)

        return X




    def aggregate_regions(self,AV):
        """ This method aggregates the supply and use table. The length of the vector AV sais how many regions there are in the model. The total number of products and industries must be a multiple of that number, else, an error is given.
        Then, the SUT is summed up according to the positions in AV. if AV[n] == x, then region n in the big SUT is aggregated into region x
        OBS: This method required the presence of U, V, Y, F, and FY. Only TL is optional.
        """
        # First, check whether the elements in AV are monotonically increasing, starting from 1:
        if (np.unique(AV) - np.arange(1,max(AV)+1,1)).sum() == 0:
            DR, StatusFlag = self.dimension_check()
            if StatusFlag == 1: # Dimensions are OK, continue
                ProdsPerRegion = len(self.V)/len(AV)
                IndusPerRegion = len(self.V[0])/len(AV)
                FDPerRegion    = len(self.Y[0])/len(AV)                
                if int(ProdsPerRegion) == ProdsPerRegion: # if the number of products is a true multiple of the number of regions
                    if int(IndusPerRegion) == IndusPerRegion: # if the number of industries is a true multiple of the number of regions
                        if int(FDPerRegion) == FDPerRegion: # if the number of final demand categories is a true multiple of the number of regions                    
                            print('Everything has proper dimensions. Aggregating SUT.')
                            NewSupply = np.zeros((ProdsPerRegion*max(AV),IndusPerRegion*max(AV)))
                            NewUse    = np.zeros((ProdsPerRegion*max(AV),IndusPerRegion*max(AV)))
                            NewF      = np.zeros((len(self.F),IndusPerRegion*max(AV)))
                            NewY      = np.zeros((ProdsPerRegion*max(AV),FDPerRegion*max(AV)))
                            NewFY     = np.zeros((len(self.F),FDPerRegion*max(AV)))                            
                            
                            SupplyIM  = np.zeros((ProdsPerRegion*max(AV),len(self.V[0])))
                            UseIM     = np.zeros((ProdsPerRegion*max(AV),len(self.U[0])))
                            YIM       = np.zeros((ProdsPerRegion*max(AV),len(self.Y[0])))
                            for m in range(0,len(AV)): # aggregate rows
                                SupplyIM[(AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] = SupplyIM[(AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] + self.V[m*ProdsPerRegion:m*ProdsPerRegion+ProdsPerRegion,:]
                                UseIM[   (AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] = UseIM[   (AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] + self.U[m*ProdsPerRegion:m*ProdsPerRegion+ProdsPerRegion,:]
                                YIM[     (AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] = YIM[     (AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] + self.Y[m*ProdsPerRegion:m*ProdsPerRegion+ProdsPerRegion,:]
                            for m in range(0,len(AV)): # aggregate columns
                                NewSupply[:,(AV[m]-1)*IndusPerRegion:(AV[m]-1)*IndusPerRegion+IndusPerRegion] = NewSupply[:,(AV[m]-1)*IndusPerRegion:(AV[m]-1)*IndusPerRegion+IndusPerRegion] + SupplyIM[:,m*IndusPerRegion:m*IndusPerRegion+IndusPerRegion]
                                NewUse[   :,(AV[m]-1)*IndusPerRegion:(AV[m]-1)*IndusPerRegion+IndusPerRegion] = NewUse[   :,(AV[m]-1)*IndusPerRegion:(AV[m]-1)*IndusPerRegion+IndusPerRegion] + UseIM[   :,m*IndusPerRegion:m*IndusPerRegion+IndusPerRegion]
                                NewY[     :,(AV[m]-1)*FDPerRegion   :(AV[m]-1)*FDPerRegion+FDPerRegion]       = NewY[     :,(AV[m]-1)*FDPerRegion   :(AV[m]-1)*FDPerRegion+FDPerRegion]       + YIM[     :,m*FDPerRegion   :m*FDPerRegion+FDPerRegion]
                                NewF[     :,(AV[m]-1)*IndusPerRegion:(AV[m]-1)*IndusPerRegion+IndusPerRegion] = NewF[     :,(AV[m]-1)*IndusPerRegion:(AV[m]-1)*IndusPerRegion+IndusPerRegion] + self.F[  :,m*IndusPerRegion:m*IndusPerRegion+IndusPerRegion]
                                if self.FY != None: # if we have findal demand extensions
                                    NewFY[:,(AV[m]-1)*FDPerRegion   :(AV[m]-1)*FDPerRegion+FDPerRegion]       = NewFY[:,(AV[m]-1)*FDPerRegion   :(AV[m]-1)*FDPerRegion+FDPerRegion]           + self.FY[ :,m*FDPerRegion   :m*FDPerRegion+FDPerRegion]
                            # assign the new values to the object
                            self.V  = NewSupply
                            self.U  = NewUse
                            self.Y  = NewY
                            self.F  = NewF
                            self.FY = NewFY
                            if self.TL != None: # Special case: If a trade link is present:
                                NewTL = np.zeros((ProdsPerRegion*max(AV),max(AV)))
                                TL_IM = np.zeros((ProdsPerRegion*max(AV),len(AV)))
                                # First, aggregate the origin regions:
                                for m in range(0,len(AV)):
                                    TL_IM[(AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] = TL_IM[(AV[m]-1)*ProdsPerRegion:(AV[m]-1)*ProdsPerRegion+ProdsPerRegion,:] + self.TL[m*ProdsPerRegion:m*ProdsPerRegion+ProdsPerRegion,:]
                                # Second, aggregate the destination regions:   
                                for m in range(0,len(AV)):                                    
                                    NewTL[:,int((AV[m]-1))] = NewTL[:,int((AV[m]-1))] + TL_IM[:,m]
                                self.TL = NewTL
                            ExitFlag = 1
                            ExitComment = 'Aggregation of regions went allright.'  
                        else:                                
                            ExitFlag = 4
                            ExitComment = 'Total number of final demand categories is not a true multiple of the number of regions.' 
                    else:
                       ExitFlag = 2 
                       ExitComment = 'Total number of industries is not a true multiple of the number of regions.' 
                else:
                    ExitFlag = 3 
                    ExitComment = 'Total number of products is not a true multiple of the number of regions.' 
            else:
               ExitFlag = 5 
               ExitComment = 'Problem with the dimensions of the SUT.'
        else: 
            ExitFlag = 0
            ExitComment = 'Problem with the sorting vector. It needs to contain all natural numbers from 1,2,3,... to its maximum value.'
        return ExitFlag, ExitComment         
        
    def remove_products_industries(self,RPV,RIV):
        """ This method sets the products with the indices in the remove-product-vector RPV to zero.
        Likewise for the industries in the remove-industy-vector RIV
        """
        # First: remove products from U, V, and Y:
        for x in RPV:
            self.U[x,:] = 0
            self.V[x,:] = 0
            if self.Y != None:
                self.Y[x,:] = 0
            # No changes to FY
            if self.TL != None:
                self.TL[x,:] = 0 # This might be problematic, since some methods require T to have at least a 1 on the diagonal
        # Second: remove industries from U, V, and F:
        for x in RIV:
            self.U[:,x] = 0
            self.V[:,x] = 0
            self.F[:,x] = 0            
        
        return 'Products and industries were removed successfully.'
             
    def _remove_empty_diagonal(self):
        """ If a diagonal entry is null, and the product is never produced, and
        the industry does not produce anything, just completely remove rows and
        columns
        """

        # Based on supply_diag_check, situations where this occurs
        keep = self.supply_diag_check()[:,4] == 0

        # Remove such empty diagonal combinations of product and industry.
        self.U = self.U[:, keep][keep, :]
        self.V = self.V[:, keep][keep, :]
        try:
            self.F = self.F[:, keep]
        except:
            pass

        try:
            self.Y = self.Y[keep,:]
        except:
            pass

    """
    Modify tables
    """

    def build_E_bar(self, prefer_exclusive=True):
        """ Determine E_bar based on V, indentifying each primary supply flow

        Makes a best guess at the primary production flow of each industry. If
        a supply flow is found on the diagonal of the supply matrix (V) pick
        this one.  Otherwise, by default, give the preference to any product
        that is exclusive to this industry, i.e. a product that is not produced
        by any other industry.  For all the rest, pick the biggest supply flows
        of each industry.

        prefer_exclusive: Default True. If false, always pick the largest
            supply flow as the primary product, even if this means creating
            more exclusive byproducts.
        """


        # Initialize zero arrays
        V_exclusive = np.zeros_like(self.V)
        V_exclusive_max = np.zeros_like(self.V)
        V_max = np.zeros_like(self.V)

        # column numbers
        cols = np.arange(self.V.shape[1])

        # If square, assume that diagonal is mainproduct whenever not null
        # Otherwise, don't assume anything
        if self.V.shape[0] == self.V.shape[1]:
            done = np.array(np.diag(self.V), dtype=bool)
            E_bar = np.array(np.diag(done), dtype=int)
        else:
            E_bar = np.zeros_like(self.V, dtype=int)
            done = np.sum(E_bar,0) != 0

        if prefer_exclusive:
            # For all other industries, if sole producer of product, make that
            # product the main product

            # Filters for exclusive products and exclusive productions of
            # interest
            V_binary = np.array(np.array(self.V, dtype=bool), dtype=int)
            exclusive_product = np.sum(V_binary, 1) == 1
            mask = np.outer(exclusive_product, ~done)

            V_exclusive[mask] = self.V[mask]
            max_in_column = np.argmax(np.abs(V_exclusive), axis=0)
            V_exclusive_max[max_in_column, cols] = V_exclusive[max_in_column, cols]

            E_bar[np.array(V_exclusive_max, dtype=bool)] = 1
            done = np.sum(E_bar,0) != 0


        # For each column without a main product, chose the largest supply flow
        max_in_column = np.argmax(np.abs(self.V), axis=0)
        V_max[max_in_column, cols] = self.V[max_in_column, cols]
        E_bar[:, ~ done] = np.array(np.array(V_max[:, ~done], dtype=bool),dtype=int)
        self.E_bar = E_bar

    def V_bar(self):
        if self.E_bar is None and (self.V.shape[0] == self.V.shape[1]):
            V_bar = ddiag(self.V)
            logging.warning("Assuming primary production is on diagonal")
        else:
            V_bar = self.V * self.E_bar

        return V_bar

    def V_tild(self):
        if self.E_bar is None and (self.V.shape[0] == self.V.shape[1]):
            V_tild = self.V - ddiag(self.V)
            logging.warning("Assuming primary production is on diagonal")
        else:
            E_tild = 1 - self.E_bar
            V_tild = self.V * E_tild

        return V_tild

    def primary_market_shares_of_regions(self):
        """ Calculate a region's share in each product's global primary supply

        For each object type, calculate the fraction that each region
        represents in its primary supply (secondary supply, as defined by
        E_tild, is excluded)

        Dependencies:
        -------------
            self.V
            self.E_bar
            self.regions

        Returns
        -------
            D: region-per-product_type matrix, with market share coefficients
                + Each column must add up to 1 (or zero if no production)

        """


        # Aggregate primary supply within each region, across industries
        V_bar = self.V_bar()
        Vagg = self.aggregate_within_regions(V_bar, axis=1)

        # Aggregate primary supply within each product group, across regions
        e = np.ones(self.regions, dtype=int)
        Vagg = self._aggregate_regions_vectorised(Vagg, e,  axis=0)

        # world-wide primary production of each product
        q_bar = np.sum(Vagg, 1)

        # Normalize regional production relative to total world production
        D = Vagg.T.dot(diaginv(q_bar))

        return D

    def build_mr_Xi(self):
        """ Define Product subtitutability matrix for multiregional system

        By default, products displace identica products produced in the same
        region. If all products were produced as primary product in all
        regions, the Xi matrix would be an identity matrix.

        Otherwise, if a product is only produced as a secondary product in a
        region, make this product substitute average primary production mix.

        Dependencies
        ------------
            self.E_bar to indicate primary production

        Returns
        -------
            self.Xi: a product*regions-by-product*region, square matrix

        """

        # By default secondary production substitutes identical product from
        # primary production in the same region
        e_bar = np.array(np.array(np.sum(self.E_bar, 1), bool), int)
        Xi = np.diag(e_bar)

        # When no local primary production to substitute, turn to global
        # primary mix
        D = self.primary_market_shares_of_regions()

        # Rearrange mix data in a region_product-by-product table
        global_mix = np.array([]).reshape(0, D.shape[1])
        for row in D:
            global_mix = np.vstack([global_mix, np.diag(row)])

        # Then tile to get same dimensions as Xi, and filter out columns where
        # Xi already has a coefficient. This gives the completementary
        # situations where the average global mix (rather than the local
        # production) get substituted
        Xi_glob = np.tile(global_mix, self.regions) * (1 - e_bar).T

        # TODO: check if there are economy-wide exclusive secondary products
        #
        # For now assume everything gets primarily produced by somebody
        # somewhere

        # Put all together and return to self
        self.Xi = Xi + Xi_glob

    def build_mr_Gamma(self):

        V_bar = self.V_bar()
        e_tild = np.array(self.E_bar.sum(1) == 0, int)


        X = self._aggregate_regions_vectorised(V_bar.T, axis=1)
        D = X.dot(diaginv(X.sum(axis=0)))

        D_tild = np.kron(np.ones(self.regions), D).dot(ddiag(e_tild))

        Dbar = V_bar.T.dot(diaginv(V_bar.sum(1)))

        self.Gamma = D_tild + Dbar



    def add_ones_to_diagonal(self): 
        """ This method adds ones where there is a zero on the diagonal of V. This is needed for simple applications of the BTC."""
        if self.V.shape[0] != self.V.shape[1]:
            return 'Error: Supply table is not square, there is no proper diagonal of that matrix.'
        else:
            for m in range(0,self.V.shape[0]):
                if self.V[m,m] == 0:
                    self.V[m,m] = 1
                    
    def clear_non_diag_supply(self):
        """ This method allows for simple application of the BTC. It removes all sectors that do not produce their respective main product."""
        if self.V.shape[0] != self.V.shape[1]:
            raise ValueError('Error: Supply table is not square, there is no proper diagonal of that matrix.')
        else:
            for m in range(0,self.V.shape[0]):
                if self.V[m,m] == 0:
                    self.V[:,m] = 0
                    self.U[:,m] = 0
                    
        
    """
    Constructs. Below, it is always assumed that U and V are present. For the industrial stressorts, F must be present as well.
    """ 
                    
#    def Build_BTC_A_matrix_extended(self):
#        """ Builds the A-matrix of the extended BTC construct
#        return: Extended A matrix for BTC construct"""
#        self.A_BTC = np.concatenate((np.concatenate((np.dot(self.U,np.linalg.inv(self.return_diag_V())),-1 * np.eye(self.V.shape[0])),axis=1), np.concatenate((np.dot(self.return_offdiag_V(),np.linalg.inv(self.return_diag_V())),np.zeros((self.V.shape[0],self.V.shape[0]))),axis=1)),axis = 0)        
#        return self.A_BTC
#        
#    def Build_BTC_L_matrix_extended(self):
#        L_prov = np.linalg.inv(np.eye(2*self.V.shape[0])-self.Build_BTC_A_matrix_extended())
#        self.L_BTC = L_prov[:,0:self.V.shape[0]]
#        return self.L_BTC
    """ General: Determine L matrix"""
    
    def Build_L_matrix(self,A):
        return np.linalg.inv(np.eye(self.V.shape[0])-A)
        
    """ byproduct technology construct (BTC)"""

    def Build_BTC_A_matrix(self,Xi = None):
        """ Builds the A-matrix of the normal BTC construct, using Xi as mapping matrix
        returns: A matrix for BTC construct
        A_BTC = (U - Xi * V_offdiag)V_diag_inv """
        if Xi == None:
            Xi = np.ones((self.V.shape))
        self.A_BTC = np.dot((self.U - Xi * self.return_offdiag_V()),np.linalg.inv(self.return_diag_V()))
        return self.A_BTC
        
    def Build_BTC_Am_matrix(self):
        """ returns use part of BTC construct: Am = UV^-1. Used to re-construct the SUT from the BTC-IO model """
        return np.dot(self.U,np.linalg.inv(self.return_diag_V()))
        
    def Build_BTC_Ab_matrix(self):
        """ returns use part of BTC construct: Ab = VoffdiagV^-1. Used to re-construct the SUT from the BTC-IO model """
        return np.dot(self.return_offdiag_V(),np.linalg.inv(self.return_diag_V()))
    
    def Build_BTC_S(self):
        """Returns stressor coefficient matrix for the BTC construct."""
        self.S_BTC = np.dot(self.F,np.linalg.inv(self.return_diag_V()))
        return self.S_BTC       
    
    """ Commodity technology construct (CTC)"""
        
    def Build_CTC_A_matrix_ixi(self):
        """ Builds the A-matrix of the CTC construct, industry-by-industry
        return: A matrix for CTC construct
        Equation taken from Miller and Blair (2009), chapter 5, Equation 5.26a
        A_CTC_ixi = g^ * V^-1 * U * g^-1"""        
        if self.V.shape[0] != self.V.shape[1]:
            raise ValueError('Error: Supply table V is not square, no matrix inversion possible.')
        else:
            try:
                V_inv = np.linalg.inv(self.V)
                try:
                    g_inv = np.linalg.inv(np.diag(self.g_V()))
                    self.A_CTC_ixi = np.dot(np.dot(np.diag(self.g_V()),V_inv),np.dot(self.U,g_inv))
                except:
                    raise ValueError('Error: Diagonal of total industry output g cannot be inverted. Singular matrix.')                        
            except:
                raise ValueError('Error: Supply table V is square, but no inverse exists.')
        return self.A_CTC_ixi
        
    def Build_CTC_A_matrix_cxc(self):
        """ Builds the A-matrix of the CTC construct, commodity-by-commodity
        return: A matrix for CTC construct
        Equation taken from Miller and Blair (2009), chapter 5, Equation 5.26
        A_CTC_cxc = U * V^-1"""        
        if self.V.shape[0] != self.V.shape[1]:
            raise ValueError('Error: Supply table V is not square, no matrix inversion possible.')
        else:
            try:
                V_inv = np.linalg.inv(self.V)
                self.A_CTC_cxc = np.dot(self.U,V_inv)
            except:
                raise ValueError('Error: Supply table V is square, but no inverse exists.')
        return self.A_CTC_cxc
        
    def Build_CTC_cxc_S(self):
        """Returns stressor coefficient matrix for the CTC cxc construct. S = F V^-1"""
        self.S_CTC_cxc = np.dot(self.F,np.linalg.inv(self.V))
        return self.S_CTC_cxc
        
    """ Industry technology construct (ITC)"""        
        
    def Build_ITC_A_matrix_ixi(self):
        """ Builds the A-matrix of the ITC construct, industry-by-industry
        return: A matrix for ITC construct
        Equation taken from Miller and Blair (2009), chapter 5, Equation 5.27a
        A_ITC_ixi = V'*q^-1  *  U * g^-1"""    

        try:
            self.g_hat_inv = np.linalg.inv(np.diag(self.g_V()))
            self.q_hat_inv = np.linalg.inv(np.diag(self.q_V()))           
            self.A_ITC_ixi = np.dot(np.dot(self.V.transpose(),self.q_hat_inv),np.dot(self.U,self.g_hat_inv))
        except:
            raise ValueError('Error: Singular matrix.')                        

        return self.A_ITC_ixi        

    def Build_ITC_A_matrix_cxc(self):
        """ Builds the A-matrix of the ITC construct, commodity-by-commodity
        return: A matrix for ITC construct
        Equation taken from Miller and Blair (2009), chapter 5, Equation 5.27
        A_ITC_cxc = U * g^-1  *  V'*q^-1 """    

        try:
            self.g_hat_inv = np.linalg.inv(np.diag(self.g_V()))
            self.q_hat_inv = np.linalg.inv(np.diag(self.q_V()))            
            self.A_ITC_cxc = np.dot(np.dot(self.U,self.g_hat_inv),np.dot(self.V.transpose(),self.q_hat_inv))
        except:
            raise ValueError('Error: Singular matrix.')                        

        return self.A_ITC_cxc
        
    def Build_ITC_cxc_S(self):
        """Returns stressor coefficient matrix for the ITC cxc construct."""
        self.S_ITC_cxc = np.dot(np.dot(self.F,np.linalg.inv(np.diag(self.g_V()))),np.dot(self.V.transpose(),np.linalg.inv(np.diag(self.q_V()))))
        return self.S_ITC_cxc        


    """ Aggregation Constructs"""        

    def pc_agg(self, keep_size=True):
        """Performs Partition Aggregation Construct of SuUT inventory

        Parameters
        ----------
        self.U : Use table [com, ind]
        self.V : Supply table [com, ind]
        self.PSI : Properties table [com, properties]
        self.PHI : Partition coefficient [ind, com (default=np.empty(0))]
        self.F : Unallocated emissions [ext, ind] (default=np.empty(0))

        Returns
        --------
        A : Normalized technical requirements [com,com]
        S : Normalized, constructed emissions [ext, com]
        nn_in : filter to remove np.empty rows in A or Z [com]
        nn_out : filter to remove np.empty columns in A or Z [com]
        Z : constructed intermediate flow matrix [com,com]
        F_con : Constructed emissions [ext,com]

        """
        # Default values
        F_con = np.empty(0)
        S = np.empty(0)

        # Partitioning properties and coefficients
        if self.PHI is None:
            self.__pa_coeff()

        # Partitioning of product flows
        Z = self.U.dot(self.PHI)  # <-- eq:PCagg

        # Partitioning of environmental extensions
        if self.F is not None:
            F_con = self.F.dot(self.PHI)  # <-- eq:PCEnvExt

        (A, S, nn_in, nn_out) = matrix_norm(Z, self.V, F_con, keep_size)

        return (A, S, nn_in, nn_out, Z, F_con)


    def psc_agg(self, keep_size=True, return_unnormalized_flows=False):
        """Performs Product Substitution aggregation Construct of SuUT inventory

        Parameters
        ----------
        U : Use table [com, ind]
        V : Supply table [com, ind]
        E_bar : 0 or 1 mapping of primary commodities to industries [com,ind]
        Xi : substitution table [com,com]
        F : Unallocated emissions [ext, ind] (default=np.empty(0))

        Returns
        --------
        A : Normalized technical requirements [com,com]
        S : Normalized, constructed emissions [ext, com]
        nn_in : filter to remove np.empty rows in A or Z [com]
        nn_out : filter to remove np.empty columns in A or Z [com]
        Z : constructed intermediate flow matrix [com,com]
        F_con : Constructed emissions [ext,com]
        """

        # Default values
        F_con = np.empty(0)
        S = np.empty(0)

        # Construction of Product Flows
        Z = (self.U - self.Xi.dot(self.V_tild())).dot(self.E_bar.T)  # <-- eq:PSCagg
        # Normalizing

        # Allocation of Environmental Extensions
        if self.F is not None:
            F_con = self.F.dot(self.E_bar.T)  # <-- eq:NonProdBalEnvExt

        (A, S, nn_in, nn_out) = matrix_norm(Z, self.V_bar(), F_con, keep_size)

        # Return allocated values
        if return_unnormalized_flows:
            logging.warning("Unnormalized flows (Z, F_con) for this construct"
                            " may differ from calculated flows for a given"
                            " final demand")
            return (A, S, nn_in, nn_out, Z, F_con)
        else:
            return (A, S, nn_in, nn_out)


    def aac_agg(self, nmax=np.Inf, res_tol=0, keep_size=True):
        """ Alternative Activity aggregation Construct of SuUT inventory

        Parameters
        ----------
        self.U : Use table [com, ind]
        self.V : Supply table [com, ind]
        self.E_bar : 0 or 1 mapping of primary commodities to industries [com,ind]
        Gamma : 0 or 1 mapping of alternate activity for each commodity
               [ind,com]
        self.F : Unallocated emissions [ext, ind] (default=np.empty(0))
        nmax : maximum number of iterative loops for defining A_gamma
               (default=Inf)

        Returns
        --------
        Z : constructed intermediate flow matrix [com,com]
        A : Normalized technical requirements [com,com]
        nn_in : filter to remove np.empty rows in A or Z [com]
        nn_out : filter to remove np.empty columns in A or Z [com]
        F_con : Constructed emissions [ext,com]
        S : Normalized, constructed emissions [ext, com]

        """
        # Default values
        F_con = np.empty(0)
        S = np.empty(0)

        # Basic variables
        e_ind = np.ones(self.V.shape[1])
        V_tild = self.V_tild()

        # Calculate competing technology requirements
        A_gamma, F_gamma = self.__alternate_tech(nmax=nmax, res_tol=res_tol)

        # Allocation step
        Z = (self.U - A_gamma.dot(V_tild)).dot(self.E_bar.T) + \
                A_gamma.dot(ddiag(V_tild.dot(e_ind)))  # <-- eq:AACagg


        # Partitioning of environmental extensions
        if self.F is not None:
            F_con = (self.F - F_gamma.dot(V_tild)).dot(self.E_bar.T) + \
                    F_gamma.dot(ddiag(V_tild.dot(e_ind)))  # <-- eq:AACEnvExt

        (A, S, nn_in, nn_out) = matrix_norm(Z, self.V, F_con, keep_size)
    #   Output
        return (A, S, nn_in, nn_out, Z, F_con)

    ##############################################################################


    def lsc(self, keep_size=True, return_unnormalized_flows=False):
        """ Performs Lump-sum aggregation Construct of SuUT inventory

        Parameters
        ----------
        self.U : Use table [com, ind]
        self.V : Supply table [com, ind]
        self.E_bar : 0 or 1 mapping of primary commodities to industries [com,ind]
        self.F : Unallocated emissions [ext, ind] (default=np.empty(0))


        Returns
        --------
        Z : constructed intermediate flow matrix [com,com]
        A : Normalized technical requirements [com,com]
        nn_in : filter to remove np.empty rows in A or Z [com]
        nn_out : filter to remove np.empty columns in A or Z [com]
        F_con : Constructed emissions [ext,com]
        S : Normalized, constructed emissions [ext, com]

        """
        # Default values
        F_con = np.empty(0)
        S = np.empty(0)

        # Allocation of Product Flows
        Z = self.U.dot(self.E_bar.T)  # <-- eq:LSCagg
        V_dd = self.E_bar.dot(ddiag(self.g_V()))  # <-- eq:LSCagg

        # Allocation of Environmental Extensions
        if self.F is not None:
            F_con = self.F.dot(self.E_bar.T)  # <-- eq:NonProdBalEnvExt

        # Normalizing
        (A, S, nn_in, nn_out) = matrix_norm(Z, V_dd, F_con, keep_size)

        # Return allocated values
        if return_unnormalized_flows:
            logging.warning("Unnormalized flows (Z, F_con) for this construct"
                            " may differ from calculated flows for a given"
                            " final demand")
            return (A, S, nn_in, nn_out, Z, F_con)
        else:
            return (A, S, nn_in, nn_out)


    ###############################################################################
    # SPECIAL CASES

    def itc(self, keep_size=True):
        """Performs Industry Technology Construct of SuUT inventory

        Parameters
        ----------
        self.U : Use table [com, ind]
        self.V : Supply table [com, ind]
        self.F : Unallocated emissions [ext, ind] (default=np.empty(0))

        Returns
        --------
        Z : constructed intermediate flow matrix [com,com]
        A : Normalized technical requirements [com,com]
        F_con : Constructed emissions [ext,com]
        S : Normalized, constructed emissions [ext, com]

        """
        # Default values
        F_con = np.empty(0)
        S = np.empty(0)

        g_diag_inv = diaginv(self.g_V())
        Z = self.U.dot(g_diag_inv).dot(self.V.T)  # <-- eq:itc

        if self.F is not None:
            F_con = self.F.dot(g_diag_inv).dot(self.V.T)  # <-- eq:ITCEnvExt

        (A, S, nn_in, nn_out) = matrix_norm(Z, self.V, F_con, keep_size)

        return (A, S, nn_in, nn_out, Z, F_con)


    def ctc(self, keep_size=True):
        """Performs Commodity Technology Construct of SuUT inventory

        Parameters
        ----------
        self.U : Use table [com, ind]
        self.V : Supply table [com, ind]
        self.F : Unallocated emissions [ext, ind] (default=np.empty(0))

        Returns
        --------
        Z : constructed intermediate flow matrix [com,com]
        A : Normalized technical requirements [com,com]
        F_con : Constructed emissions [ext,com]
        S : Normalized, constructed emissions [ext, com]

        """
        # Default values
        F_con = np.empty(0)
        S = np.empty(0)

        inv_V = np.linalg.inv(self.V)
        A = self.U.dot(inv_V)  # <-- eq:ctc
        Z = A.dot(ddiag(self.q_V()))

        if self.F is not None:
            S = self.F.dot(inv_V)
            F_con = S.dot(ddiag(self.q_V()))  # <--eq:CTCEnvExt

        nn_in, nn_out = matrix_norm(Z, self.V, just_filters=True)

        return (A, S, nn_in, nn_out, Z, F_con)


    def btc(self, keep_size=True):
        """Performs Byproduct Technology Construct of SuUT inventory
        Parameters
        ----------
        self.U : Use table [com, ind]
        self.V : Supply table [com, ind]
        self.E_bar : 0 or 1 mapping of primary commodities to industries [com,ind]
        self.F : Unallocated emissions [ext, ind] (default=np.empty(0))

        Returns
        --------
        Z : constructed intermediate flow matrix [com,com]
        A : Normalized technical requirements [com,com]
        F_con : Constructed emissions [ext,com]
        S : Normalized, constructed emissions [ext, com]

        """

        # Default values
        F_con = np.empty(0)
        S = np.empty(0)

        if self.E_bar is None and (self.V.shape[0] == self.F.shape[1]):
            E_bar = np.eye(self.V.shape[0])
        else:
            E_bar = self.E_bar

        # The construct
        Z = (self.U - self.V_tild()).dot(E_bar.T)  # <-- eq:btc

        if self.F is not None:
            F_con = self.F.dot(E_bar.T)  # <-- eq:NonProdBalEnvExt

        (A, S, nn_in, nn_out) = matrix_norm(Z, self.V_bar(), F_con, keep_size)

        return (A, S, nn_in, nn_out, Z, F_con)

    """ HELPER FUNCTIONS"""
    def __pa_coeff(self):
        """Calculates partition coefficients from supply and properties table

        Parameters
        ----------
        self.V : Supply table [com, ind]
        self.PSI : Properties table [com, properties]

        Returns
        --------
        self.PHI : Partition coefficient [ind, com (default=np.empty(0))]
            Properties in self.PSI should be intensive properties (e.g. energy density,
            price etc., not extensive properties such as energy content, value, or
            mass

        """
        # Calculate total amount of the partition property that is output by each
        # industry (total mass output for all commodities supplied by ind. J)
        denominator = ddiag(self.V.T.dot(self.PSI))

        # Calculate the share of this total output of property that is mediated by
        # each output (share of total mass output by ind. J that happens via
        # commodity j.
        self.PHI = np.linalg.inv(denominator).dot(self.V.T * self.PSI.T)



    def __alternate_tech(self, nmax=np.Inf, lay=None, res_tol=1e-30):
        """Compilation of Alternate Technologies for use in AAA and AAC models

        Parameters
        ----------
        X : Use table [com, ind] or [org, com, ind]
        self.V : Supply table [com, ind]
        self.E_bar : mapping of primary commodities to industries [com,ind]
        Gamma : mapping of alternate producer for each commodity [ind,com]
        nmax : maximum number of iterations, as this search for alternative
           technologies is not garanteed to suceed

        Returns
        --------
        A_gamma : the selected alternative technology that will be assumed for
            each secondary production


        """

        # Basic variables
        # (com, _, org, traceable, e_com, _, _, self.g_V(), _) = basic_variables(X, self.V)
        #
        com = self.V.shape[0]
        traceable = False
        org = 1 # check on this
        e_com = np.ones(com)
        V_tild = self.V_tild()
        V_bar = self.V_bar()
        Gamma = self.Gamma

        # If a property layer is defined for Gamma, then evaluate unit conversion
        if Gamma.ndim == 3:
            if lay is None:
                raise TypeError('expected a value for lay')
            s = Gamma.shape
            tmp = np.zeros((s[0], s[2]))
            for i in range(Gamma.shape[1]):
                tmp += diaginv(lay[i, :].dot(self.E_bar)).dot(Gamma[:, i, :]).dot(
                        ddiag(lay[i, :]))
            Gamma = tmp

        so = np.array(np.sum(self.V != 0, 0) == 1, dtype=int)
        mo = np.array(np.sum(self.V != 0, 0) != 1, dtype=int)

        invg = diaginv(self.g_V())
        M = V_tild.dot(diaginv(e_com.dot(V_bar)))

        # Iteration 0: Prepare summation term used in definition of A_gamma
        n = 0
        tier = -1 * Gamma.dot(M)
        tier_n = np.linalg.matrix_power(tier, n)   # simplifies to identity matrix
        theSum = tier_n.dot(Gamma)
        n = n + 1
        res = np.sum(tier_n)

        # Iterations 1 to nmax
        while ((res > res_tol) or (res < 0)) and (n <= nmax):
            tier_n = tier_n.dot(tier)
            theSum += tier_n.dot(Gamma)
            n += 1
            res = np.sum(tier_n)
            print("residual:{}".format(res))
        print("number of iterations:{}".format(n))

        def apply_to_requirements(X):
            if not traceable:
                B = X.dot(invg)
                B_so = B.dot(ddiag(so))

                N = X.dot(diaginv(e_com.dot(V_bar)))
                N_so = N.dot(ddiag(mo))

                X_gamma = (B_so + N_so).dot(theSum)

            else:
                X_gamma = np.zeros([org, com, com])
                for I in range(org):
                    Bo = X[I, :, :].dot(invg)
                    Bo_so = Bo.dot(ddiag(so))
                    No = X[I, :, :].dot(diaginv(e_com.dot(V_bar)))
                    No_mo = No.dot(ddiag(mo))
                    X_gamma[I, :, :] = (Bo_so + No_mo).dot(theSum)

            return X_gamma

        A_gamma = apply_to_requirements(self.U)
        if self.F is not None:
            S_gamma = apply_to_requirements(self.F)
        else:
            S_gamma = np.empty(0)

        return(A_gamma, S_gamma)

#
# Helper functions outside object
def collapse_dims(x, first2dimensions=False):
    """Collapse 3-d or 4-d array in two dimensions

    Parameters
    ----------
    x : 3d or 4d array to be collapsed

    first2dimensions : Boolean : For 3d array, should the last two dimensions
        be flattened together (default) or should the first two be
        flattened together instead (=true)?

    Returns
    --------
    z : Flatened 2d array

    """

    s = x.shape
    if x.ndim == 4:
        z = x.reshape((s[0] * s[1], s[2] * s[3]))
    elif x.ndim == 3:
        if first2dimensions:
            z = x.reshape((s[0] * s[1], s[2]))
        else:
            z = x.reshape((s[0], s[1] * s[2]))
    elif x.ndim == 2:
        print('Already in 2-dimensional, pass')
        z = x
    else:
        print('PROBLEM? ndim(Y) = {}'.format(x.ndim))
    return z



def matrix_norm(Z, V, F_con=np.empty(0), keep_size=False, just_filters=False):
    """ Normalizes a flow matrices, even if some rows and columns are null

    Processes product flows (Z) and environmental extensions (F_con).
    Normalizes columns for which a product is indeed supplied, and remove rows
    and columns of products that are not produced (nan-columns).

    For readability, also remove rows of products that are not used

    If keep_size: don't remove an rows or columns, fill with zeros if nan.

    Parameters
    ----------
    Z : Flow matrix to be normalized
        dimensions : [com, com] | [com, ind, com] | [ind,com,ind,com]
    V : Production volume with which flows are normalized
        [com, ind]

    F_con: Allocated or construced but unnormalized environmental extensions
           [str, com] | [str, ind, com]

    keep_size: Do not remove empty rows and columns from A, leave with
                   zeros. [Default, false, don't do it]

    just_filters: Don't normalize anything, just return nn_in and nn_out


    Returns (when just_filters==False, otherwise just last two)
    --------
    A : Normalized flow matrix, without null/nan rows and nan columns
    S : Normalized extensions, by default without nan columns
    nn_in : filter applied to rows (0 for removed rows, 1 for kept rows)
    nn_out : filter applied to cols (0 for removed cols, 1 for kept cols)

    """
    # Collapse dimensions
    if Z.ndim > 2:
        Z = collapse_dims(Z)
    if F_con.ndim > 2:
        F_con = collapse_dims(F_con)

    # Basic Variables
    com = np.size(V, 0)
    ind = np.size(V, 1)
    com2 = np.size(Z, 0)

    # Total production (q, q_tr) and intermediate consumptin (u) vectors
    q = np.sum(V, 1)
    u = np.sum(Z, 1)
    if np.max(Z.shape) == com * ind:
        q_tr = np.zeros(ind * com)
        for i in range(ind):
            q_tr[i * com:(i + 1) * com] = V[:, i]

    if np.size(Z, 0) == com:
        traceable = False
        nn_in = (abs(q) + abs(u)) != 0
    elif np.size(Z, 0) == com * ind:
        traceable = True
        nn_in = (abs(q_tr) + abs(u)) != 0
    else:
        raise Exception("Mismatched rows between Z and V")

    if np.size(Z, 1) == com:
        nn_out = q != 0
        q_inv = np.linalg.inv(ddiag(q[nn_out]))
    elif np.size(Z, 1) == com * ind:
        nn_out = q_tr != 0
        q_inv = np.linalg.inv(ddiag(q_tr[nn_out]))
    else:
        raise Exception("Mismatched columns between Z and V")


    # Filter inputs. Preserve only commodities that are used (to get the recipe
    # right) or that are produced (to get the whole matrix square)
    if just_filters:
        return (nn_in, nn_out)

    # remove empty entried, diagonalize, inverse...
    if np.size(Z, 1) == com:
        q_inv = np.linalg.inv(ddiag(q[nn_out]))
    else:
        q_inv = np.linalg.inv(ddiag(q_tr[nn_out]))

    # and use to normalize product and stressor flows.
    A = Z[nn_in, :][:, nn_out].dot(q_inv)
    if F_con.size:
        S = F_con[:, nn_out].dot(q_inv)
    else:
        S = np.empty(0)

    # Restore size if need be
    if keep_size:
        A = restore_size(A, nn_in, nn_out)
        S = restore_size(S, nn_out=nn_out)

    # Return
    return (A, S, nn_in, nn_out)

def restore_size(X, nn_in=None, nn_out=None):

    # Make sure we have somthing significant
    if not X.size:
        return X

    # Restore  rows
    if nn_in is not None:
        X0 = np.zeros((len(nn_in), X.shape[1]))
        X0[nn_in, :] = X
    else:
        X0 = X

    # Restore cols
    if nn_out is not None:
        X1 = np.zeros((X0.shape[0], len(nn_out)))
        X1[:, nn_out] = X0
    else:
        X1 = X0

    return X1


def diaginv(x):
    """Diagonalizes a vector and inverses it, even if it contains zero values.

    * Element-wise divide a vector of ones by x
    * Replace any instance of Infinity by 0
    * Diagonalize the resulting vector

    Parameters
    ----------
    x : vector to be diagonalized

    Returns
    --------
    y : diagonalized and inversed vector
       Values on diagonal = 1/coefficient, or 0 if coefficient == 0

    """
    y = np.ones(len(x)) / x
    y[y == np.Inf] = 0
    return ddiag(y)

def ddiag(a, nozero=False):
    """ Robust diagonalization : always put selected diagonal on a diagonal!

    This small function aims at getting a behaviour closer to the
    mathematical "hat", compared to what np.diag() can delivers.

    If applied to a vector or a 2d-matrix with one dimension of size 1, put
    the coefficients on the diagonal of a matrix with off-diagonal elements
    equal to zero.

    If applied to a 2d-matrix (with all dimensions of size > 1), replace
    all off-diagonal elements by zeros.

    Parameters
    ----------
    a : numpy matrix or vector to be diagonalized

    Returns
    --------
    b : Diagonalized vector

    Raises:
       ValueError if a is more than 2dimensional

    See Also
    --------
        diag
    """

    # If numpy vector
    if a.ndim == 1:
        b = np.diag(a)

    # If numpy 2d-array
    elif a.ndim == 2:

        #...but with dimension of magnitude 1
        if min(a.shape) == 1:
            b = np.diag(np.squeeze(a))

        # ... or a "true" 2-d matrix
        else:
            b = np.diag(np.diag(a))

    else:
        raise ValueError("Input must be 1- or 2-d")

    # Extreme case: a 1 element matrix/vector
    if b.ndim == 1 & b.size == 1:
        b = b.reshape((1, 1))

    if nozero:
        # Replace offdiagonal zeros by nan if desired
        c = np.empty_like(b) *  np.nan
        di = np.diag_indices_from(c)
        c[di] = b.diagonal()
        return c
    else:
        # A certainly diagonal vector is returned
        return b

"""
End of file
"""
