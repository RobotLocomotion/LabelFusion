if [ -z $LABELFUSION_SOURCE_DIR ]; then
  echo "You must set LABELFUSION_SOURCE_DIR before sourcing this file."
  return
fi

if [ -z $DIRECTOR_INSTALL_DIR ]; then
  echo "You must set DIRECTOR_INSTALL_DIR before sourcing this file."
  return
fi

export PYTHONPATH=$PYTHONPATH:$LABELFUSION_SOURCE_DIR/modules
export PATH=$LABELFUSION_SOURCE_DIR/scripts/bin:$LABELFUSION_SOURCE_DIR/automation/scripts/bin:$DIRECTOR_INSTALL_DIR/bin:$PATH
export ELASTIC_FUSION_EXECUTABLE=$DIRECTOR_INSTALL_DIR/bin/ElasticFusion

export FGR_BASE_DIR=$HOME/software_tools/FastGlobalRegistration
export GOICP_BASE_DIR=$HOME/software_tools/GoICP_V1.3
export SUPER4PCS_BASE_DIR=$HOME/software_tools/nmellado-Super4PCS-c77cc4a

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIRECTOR_INSTALL_DIR/lib


cdlf()
{
    cd $LABELFUSION_SOURCE_DIR
}
export -f cdlf 
