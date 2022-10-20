*KEYWORD
$# *CONTROL_TERMINATION
$# $$  ENDTIM    ENDCYC     DTMIN    ENDENG    ENDMAS
$#      100.0         0       0.0       0.0       0.0
*CONTROL_MPP_IO_NOD3DUMP
*CONTROL_TIMESTEP
$$  DTINIT    TSSFAC      ISDO    TSLIMT     DT2MS      LCTM     ERODE     MSIST
       0.0       0.9         0       0.0-1.000E-03         0         0         0
       0.0         0         0
*CONTROL_SHELL
$$  WRPANG     ESORT     IRNXX    ISTUPD    THEORY       BWC     MITER      PROJ
      20.0         1        -1         1         2         2         1         0
$$ ROTASCL    INTGRD    LAMSHT    CSTYP6    THSHEL
       1.0         0         0         1         0
$$ PSSTUPD   SIDT4TU     CNTCO    ITSFLG    IRQUAD
         0                                        
$$  NFAIL1    NFAIL4   PSNFAIL    KEEPCS     DELFR   DRCPSID    DRCPRM
                                                                      
*CONTROL_HOURGLASS
$$     IHQ        QH
         1      0.12
*CONTROL_SOLID
$$   ESORT    FMATRX   NIPTETS    SWLOCL
         1         0         0         2
$$   PM1     PM2     PM3     PM4     PM5     PM6     PM7     PM8     PM9    PM10
       0       0       0       0       0       0       0       0       0       0
*CONTROL_BULK_VISCOSITY
$$      Q1        Q2        IBQ
       1.5      0.06        -2
*CONTROL_CONTACT
$$  SLSFAC    RWPNAL    ISLCHK    SHLTHK    PENOPT    THKCHG     ORIEN    ENMASS
       0.1       1.0         2         1         0         0         1         0
$$  USRSTR    USRFRC     NSBCS    INTERM     XPENE     SSTHK      ECDT   TIEDPRJ
         0         0         0         0       4.0         0         0         0
$$   SFRIC     DFRIC       EDC    INTVFC        TH     TH_SF    PEN_SF
       0.0       0.0       0.0       0.0       0.0       0.0       0.0
$$  IGNORE    FRCENG   SKIPRWG    OUTSEG   SPOTSTP   SPOTDEL   SPOTHIN
         1         0         0         0         0         0       0.0
$$    ISYM    NSEROD    RWGAPS    RWGDTH     RWKSF      ICOV    SWRADF    ITHOFF
         0         0         0       0.0       1.0         0       0.0         0
$$  SHLEDG    PSTIFF    ITHCNT    TDCNOF     FTALL              SHLTRW          
         0         0         0         0         0                 0.0          
*CONTROL_OUTPUT
$$   NPOPT    NEECHO    NREFUP    IACCOP     OPIFS    IPNINT    IKEDIT
         0         0         1         0       0.0         0       100      5000
         0         0         2        50         0
*CONTROL_ENERGY
$$    HGEN      RWEN    SLNTEN     RYLEN
         2         2         2         2
*CONTROL_ACCURACY
$$ OSU           INN    PIDOSU
         0         4         0
*CONTROL_SOLUTION
$$    SOLN
         0         0         1         0
$$DATABASE_OPTION -- Control Cards for ASCII output
*DATABASE_ABSTAT
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_BNDOUT
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_DEFORC
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_ELOUT
$$      DT    BINARY      LCUR      IOPT
       1.0         3                    
*DATABASE_GLSTAT
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_JNTFORC
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_MATSUM
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_NODFOR
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_NODOUT
$$      DT    BINARY      LCUR      IOPT      DTHF     BINHF
       0.1         3                                        
*DATABASE_RBDOUT
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_RCFORC
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_SBTOUT
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_SECFORC
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_SLEOUT
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_SPCFORC
$$      DT    BINARY      LCUR      IOPT
       0.1         3                    
*DATABASE_BINARY_D3PLOT
$$ DT/CYCL      LCDT      BEAM     NPLTC    PSETID
       2.0         0         0         0         0
         0
*END
