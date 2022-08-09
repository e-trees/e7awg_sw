Search.setIndex({docnames:["e7awgsw","e7awgsw.labrad","index","modules"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":4,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,"sphinx.ext.viewcode":1,sphinx:56},filenames:["e7awgsw.rst","e7awgsw.labrad.rst","index.rst","modules.rst"],objects:{"":[[0,0,0,"-","e7awgsw"]],"e7awgsw.awgctrl":[[0,1,1,"","AwgCtrl"],[0,1,1,"","AwgCtrlBase"]],"e7awgsw.awgctrl.AwgCtrl":[[0,2,1,"","__init__"],[0,2,1,"","close"]],"e7awgsw.awgctrl.AwgCtrlBase":[[0,3,1,"","MAX_WAVE_REGISTRY_ENTRIES"],[0,3,1,"","SAMPLING_RATE"],[0,2,1,"","__init__"],[0,2,1,"","check_err"],[0,2,1,"","clear_awg_stop_flags"],[0,2,1,"","get_wave_startable_block_timing"],[0,2,1,"","initialize"],[0,2,1,"","register_wave_sequences"],[0,2,1,"","reset_awgs"],[0,2,1,"","set_wave_sequence"],[0,2,1,"","set_wave_startable_block_timing"],[0,2,1,"","start_awgs"],[0,2,1,"","terminate_awgs"],[0,2,1,"","version"],[0,2,1,"","wait_for_awgs_to_stop"]],"e7awgsw.awgwave":[[0,1,1,"","GaussianPulse"],[0,1,1,"","IqWave"],[0,1,1,"","ParameterizedWave"],[0,1,1,"","SawtoothWave"],[0,1,1,"","SinWave"],[0,1,1,"","SquareWave"]],"e7awgsw.awgwave.GaussianPulse":[[0,2,1,"","__init__"],[0,4,1,"","duration"],[0,2,1,"","gen_samples"],[0,4,1,"","variance"]],"e7awgsw.awgwave.IqWave":[[0,2,1,"","__init__"],[0,2,1,"","convert_to_iq_format"],[0,2,1,"","gen_samples"],[0,4,1,"","i_wave"],[0,4,1,"","q_wave"]],"e7awgsw.awgwave.ParameterizedWave":[[0,2,1,"","__init__"],[0,4,1,"","amplitude"],[0,4,1,"","frequency"],[0,2,1,"","gen_samples"],[0,4,1,"","num_cycles"],[0,4,1,"","offset"],[0,4,1,"","phase"]],"e7awgsw.awgwave.SawtoothWave":[[0,2,1,"","__init__"],[0,4,1,"","crest_pos"],[0,2,1,"","gen_samples"]],"e7awgsw.awgwave.SinWave":[[0,2,1,"","__init__"],[0,2,1,"","gen_samples"]],"e7awgsw.awgwave.SquareWave":[[0,2,1,"","__init__"],[0,4,1,"","duty_cycle"],[0,2,1,"","gen_samples"]],"e7awgsw.capturectrl":[[0,1,1,"","CaptureCtrl"],[0,1,1,"","CaptureCtrlBase"]],"e7awgsw.capturectrl.CaptureCtrl":[[0,2,1,"","__init__"],[0,2,1,"","close"]],"e7awgsw.capturectrl.CaptureCtrlBase":[[0,3,1,"","CAPTURE_DATA_ALIGNMENT_SIZE"],[0,3,1,"","MAX_CAPTURE_PARAM_REGISTRY_ENTRIES"],[0,3,1,"","MAX_CAPTURE_SAMPLES"],[0,3,1,"","MAX_CLASSIFICATION_RESULTS"],[0,3,1,"","SAMPLING_RATE"],[0,2,1,"","__init__"],[0,2,1,"","check_err"],[0,2,1,"","clear_capture_stop_flags"],[0,2,1,"","disable_start_trigger"],[0,2,1,"","enable_start_trigger"],[0,2,1,"","get_capture_data"],[0,2,1,"","get_classification_results"],[0,2,1,"","initialize"],[0,2,1,"","num_captured_samples"],[0,2,1,"","register_capture_params"],[0,2,1,"","reset_capture_units"],[0,2,1,"","select_trigger_awg"],[0,2,1,"","set_capture_params"],[0,2,1,"","start_capture_units"],[0,2,1,"","version"],[0,2,1,"","wait_for_capture_units_to_stop"]],"e7awgsw.captureparam":[[0,1,1,"","CaptureParam"]],"e7awgsw.captureparam.CaptureParam":[[0,3,1,"","MAX_CAPTURE_DELAY"],[0,3,1,"","MAX_DECISION_FUNC_COEF_VAL"],[0,3,1,"","MAX_DECISION_FUNC_CONST_VAL"],[0,3,1,"","MAX_FIR_COEF_VAL"],[0,3,1,"","MAX_INTEG_SECTIONS"],[0,3,1,"","MAX_POST_BLANK_LEN"],[0,3,1,"","MAX_SUM_RANGE_LEN"],[0,3,1,"","MAX_SUM_SECTIONS"],[0,3,1,"","MAX_SUM_SECTION_LEN"],[0,3,1,"","MAX_WINDOW_COEF_VAL"],[0,3,1,"","MIN_DECISION_FUNC_COEF_VAL"],[0,3,1,"","MIN_DECISION_FUNC_CONST_VAL"],[0,3,1,"","MIN_FIR_COEF_VAL"],[0,3,1,"","MIN_WINDOW_COEF_VAL"],[0,3,1,"","NUM_COMPLEXW_WINDOW_COEFS"],[0,3,1,"","NUM_COMPLEX_FIR_COEFS"],[0,3,1,"","NUM_REAL_FIR_COEFS"],[0,3,1,"","NUM_SAMPLES_IN_ADC_WORD"],[0,2,1,"","__init__"],[0,2,1,"","add_sum_section"],[0,2,1,"","calc_capture_samples"],[0,2,1,"","calc_required_capture_mem_size"],[0,4,1,"","capture_delay"],[0,2,1,"","clear_sum_sections"],[0,4,1,"","complex_fir_coefs"],[0,4,1,"","complex_window_coefs"],[0,2,1,"","del_sum_section"],[0,4,1,"","dsp_units_enabled"],[0,2,1,"","get_decision_func_params"],[0,4,1,"","num_integ_sections"],[0,4,1,"","num_samples_to_process"],[0,2,1,"","num_samples_to_sum"],[0,4,1,"","num_sum_sections"],[0,4,1,"","num_words_to_sum"],[0,4,1,"","real_fir_i_coefs"],[0,4,1,"","real_fir_q_coefs"],[0,2,1,"","sel_dsp_units_to_enable"],[0,2,1,"","set_decision_func_params"],[0,2,1,"","sum_section"],[0,4,1,"","sum_section_list"],[0,4,1,"","sum_start_word_no"]],"e7awgsw.exception":[[0,5,1,"","AwgTimeoutError"],[0,5,1,"","CaptureUnitTimeoutError"],[0,5,1,"","SequencerTimeoutError"],[0,5,1,"","TooLittleFreeSpaceInCmdFifoError"]],"e7awgsw.hwdefs":[[0,1,1,"","AWG"],[0,1,1,"","AwgErr"],[0,1,1,"","CaptureErr"],[0,1,1,"","CaptureModule"],[0,1,1,"","CaptureParamElem"],[0,1,1,"","CaptureUnit"],[0,1,1,"","DecisionFunc"],[0,1,1,"","DspUnit"],[0,1,1,"","FeedbackChannel"],[0,1,1,"","SequencerErr"]],"e7awgsw.hwdefs.AWG":[[0,3,1,"","U0"],[0,3,1,"","U1"],[0,3,1,"","U10"],[0,3,1,"","U11"],[0,3,1,"","U12"],[0,3,1,"","U13"],[0,3,1,"","U14"],[0,3,1,"","U15"],[0,3,1,"","U2"],[0,3,1,"","U3"],[0,3,1,"","U4"],[0,3,1,"","U5"],[0,3,1,"","U6"],[0,3,1,"","U7"],[0,3,1,"","U8"],[0,3,1,"","U9"],[0,2,1,"","all"],[0,2,1,"","includes"],[0,2,1,"","of"]],"e7awgsw.hwdefs.AwgErr":[[0,3,1,"","MEM_RD"],[0,3,1,"","SAMPLE_SHORTAGE"],[0,2,1,"","all"],[0,2,1,"","includes"]],"e7awgsw.hwdefs.CaptureErr":[[0,3,1,"","MEM_WR"],[0,3,1,"","OVERFLOW"],[0,2,1,"","all"],[0,2,1,"","includes"]],"e7awgsw.hwdefs.CaptureModule":[[0,3,1,"","U0"],[0,3,1,"","U1"],[0,2,1,"","all"],[0,2,1,"","get_units"],[0,2,1,"","includes"],[0,2,1,"","of"]],"e7awgsw.hwdefs.CaptureParamElem":[[0,3,1,"","CAPTURE_DELAY"],[0,3,1,"","COMP_FIR_COEF"],[0,3,1,"","COMP_WINDOW_COEF"],[0,3,1,"","DICISION_FUNC_PARAM"],[0,3,1,"","DSP_UNITS"],[0,3,1,"","NUM_INTEG_SECTIONS"],[0,3,1,"","NUM_SUM_SECTIONS"],[0,3,1,"","POST_BLANK_LEN"],[0,3,1,"","REAL_FIR_COEF"],[0,3,1,"","SUM_SECTION_LEN"],[0,3,1,"","SUM_TARGET_INTERVAL"],[0,2,1,"","all"],[0,2,1,"","includes"]],"e7awgsw.hwdefs.CaptureUnit":[[0,3,1,"","U0"],[0,3,1,"","U1"],[0,3,1,"","U2"],[0,3,1,"","U3"],[0,3,1,"","U4"],[0,3,1,"","U5"],[0,3,1,"","U6"],[0,3,1,"","U7"],[0,2,1,"","all"],[0,2,1,"","includes"],[0,2,1,"","of"]],"e7awgsw.hwdefs.DecisionFunc":[[0,3,1,"","U0"],[0,3,1,"","U1"],[0,2,1,"","all"],[0,2,1,"","includes"],[0,2,1,"","of"]],"e7awgsw.hwdefs.DspUnit":[[0,3,1,"","CLASSIFICATION"],[0,3,1,"","COMPLEX_FIR"],[0,3,1,"","COMPLEX_WINDOW"],[0,3,1,"","DECIMATION"],[0,3,1,"","INTEGRATION"],[0,3,1,"","REAL_FIR"],[0,3,1,"","SUM"],[0,2,1,"","all"],[0,2,1,"","includes"]],"e7awgsw.hwdefs.FeedbackChannel":[[0,3,1,"","U0"],[0,3,1,"","U1"],[0,3,1,"","U2"],[0,3,1,"","U3"],[0,3,1,"","U4"],[0,3,1,"","U5"],[0,3,1,"","U6"],[0,3,1,"","U7"],[0,2,1,"","all"],[0,2,1,"","includes"],[0,2,1,"","of"]],"e7awgsw.hwdefs.SequencerErr":[[0,3,1,"","CMD_FIFO_OVERFLOW"],[0,3,1,"","ERR_FIFO_OVERFLOW"],[0,2,1,"","all"],[0,2,1,"","includes"]],"e7awgsw.labrad":[[1,1,1,"","RemoteAwgCtrl"],[1,1,1,"","RemoteCaptureCtrl"],[1,0,0,"-","awgcapture_server"],[1,0,0,"-","remoteawgctrl"],[1,0,0,"-","remotecapturectrl"]],"e7awgsw.labrad.RemoteAwgCtrl":[[1,2,1,"","__init__"],[1,2,1,"","disconnect"]],"e7awgsw.labrad.RemoteCaptureCtrl":[[1,2,1,"","__init__"],[1,2,1,"","disconnect"]],"e7awgsw.labrad.awgcapture_server":[[1,1,1,"","AwgCaptureServer"]],"e7awgsw.labrad.awgcapture_server.AwgCaptureServer":[[1,2,1,"","__init__"],[1,2,1,"","awg_version"],[1,2,1,"","capture_unit_version"],[1,2,1,"","check_awg_err"],[1,2,1,"","check_capture_unit_err"],[1,2,1,"","clear_awg_stop_flags"],[1,2,1,"","clear_capture_stop_flags"],[1,2,1,"","create_awgctrl"],[1,2,1,"","create_capturectrl"],[1,2,1,"","disable_start_trigger"],[1,2,1,"","discard_awgctrl"],[1,2,1,"","discard_capturectrl"],[1,2,1,"","enable_start_trigger"],[1,2,1,"","get_capture_data"],[1,2,1,"","get_classification_results"],[1,2,1,"","get_wave_startable_block_timing"],[1,2,1,"","initialize_awgs"],[1,2,1,"","initialize_capture_units"],[1,3,1,"","name"],[1,2,1,"","num_captured_samples"],[1,2,1,"","reset_awgs"],[1,2,1,"","reset_capture_units"],[1,2,1,"","select_trigger_awg"],[1,2,1,"","set_capture_params"],[1,2,1,"","set_wave_sequence"],[1,2,1,"","set_wave_startable_block_timing"],[1,2,1,"","start_awgs"],[1,2,1,"","start_capture_units"],[1,2,1,"","terminate_awgs"],[1,2,1,"","wait_for_awgs_to_stop"],[1,2,1,"","wait_for_capture_units_to_stop"]],"e7awgsw.labrad.remoteawgctrl":[[1,1,1,"","RemoteAwgCtrl"]],"e7awgsw.labrad.remoteawgctrl.RemoteAwgCtrl":[[1,2,1,"","__init__"],[1,2,1,"","disconnect"]],"e7awgsw.labrad.remotecapturectrl":[[1,1,1,"","RemoteCaptureCtrl"]],"e7awgsw.labrad.remotecapturectrl.RemoteCaptureCtrl":[[1,2,1,"","__init__"],[1,2,1,"","disconnect"]],"e7awgsw.lock":[[0,1,1,"","ReentrantFileLock"]],"e7awgsw.lock.ReentrantFileLock":[[0,2,1,"","__init__"],[0,2,1,"","acquire"],[0,2,1,"","discard"],[0,2,1,"","release"]],"e7awgsw.sequencer":[[0,1,1,"","SequencerCtrl"],[0,1,1,"","SequencerCtrlBase"]],"e7awgsw.sequencer.SequencerCtrl":[[0,2,1,"","__init__"],[0,2,1,"","close"]],"e7awgsw.sequencer.SequencerCtrlBase":[[0,2,1,"","__init__"],[0,2,1,"","check_err"],[0,2,1,"","clear_suquencer_stop_flag"],[0,2,1,"","clear_unprocessed_commands"],[0,2,1,"","clear_unsent_cmd_err_reports"],[0,2,1,"","cmd_fifo_free_space"],[0,2,1,"","disable_cmd_err_report"],[0,2,1,"","enable_cmd_err_report"],[0,2,1,"","initialize"],[0,2,1,"","num_cmd_err_reports"],[0,2,1,"","num_err_commands"],[0,2,1,"","num_succeeded_commands"],[0,2,1,"","num_unprocessed_commands"],[0,2,1,"","pop_cmd_err_reports"],[0,2,1,"","push_commands"],[0,2,1,"","start_sequencer"],[0,2,1,"","terminate_sequencer"],[0,2,1,"","version"],[0,2,1,"","wait_for_sequencer_to_stop"]],"e7awgsw.sequencercmd":[[0,1,1,"","AwgStartCmd"],[0,1,1,"","AwgStartCmdErr"],[0,1,1,"","CaptureAddrSetCmd"],[0,1,1,"","CaptureAddrSetCmdErr"],[0,1,1,"","CaptureEndFenceCmd"],[0,1,1,"","CaptureEndFenceCmdErr"],[0,1,1,"","CaptureParamSetCmd"],[0,1,1,"","CaptureParamSetCmdErr"],[0,1,1,"","FeedbackCalcOnClassificationCmd"],[0,1,1,"","FeedbackCalcOnClassificationCmdErr"],[0,1,1,"","SequencerCmd"],[0,1,1,"","SequencerCmdErr"],[0,1,1,"","WaveSequenceSetCmd"],[0,1,1,"","WaveSequenceSetCmdErr"]],"e7awgsw.sequencercmd.AwgStartCmd":[[0,3,1,"","ID"],[0,3,1,"","MAX_START_TIME"],[0,2,1,"","__init__"],[0,4,1,"","awg_id_list"],[0,2,1,"","serialize"],[0,2,1,"","size"],[0,4,1,"","start_time"]],"e7awgsw.sequencercmd.AwgStartCmdErr":[[0,2,1,"","__init__"],[0,4,1,"","awg_id_list"]],"e7awgsw.sequencercmd.CaptureAddrSetCmd":[[0,3,1,"","ID"],[0,2,1,"","__init__"],[0,4,1,"","byte_offset"],[0,4,1,"","capture_unit_id_list"],[0,2,1,"","serialize"],[0,2,1,"","size"]],"e7awgsw.sequencercmd.CaptureAddrSetCmdErr":[[0,2,1,"","__init__"],[0,4,1,"","write_err"]],"e7awgsw.sequencercmd.CaptureEndFenceCmd":[[0,3,1,"","ID"],[0,3,1,"","MAX_END_TIME"],[0,2,1,"","__init__"],[0,4,1,"","capture_unit_id_list"],[0,4,1,"","end_time"],[0,2,1,"","serialize"],[0,2,1,"","size"],[0,4,1,"","terminate"],[0,4,1,"","wait"]],"e7awgsw.sequencercmd.CaptureEndFenceCmdErr":[[0,2,1,"","__init__"],[0,4,1,"","capture_unit_id_list"]],"e7awgsw.sequencercmd.CaptureParamSetCmd":[[0,3,1,"","ID"],[0,2,1,"","__init__"],[0,4,1,"","capture_unit_id_list"],[0,4,1,"","feedback_channel_id"],[0,4,1,"","key_table"],[0,4,1,"","param_elems"],[0,2,1,"","serialize"],[0,2,1,"","size"]],"e7awgsw.sequencercmd.CaptureParamSetCmdErr":[[0,2,1,"","__init__"],[0,4,1,"","read_err"],[0,4,1,"","write_err"]],"e7awgsw.sequencercmd.FeedbackCalcOnClassificationCmd":[[0,3,1,"","ID"],[0,2,1,"","__init__"],[0,4,1,"","byte_offset"],[0,4,1,"","capture_unit_id_list"],[0,4,1,"","elem_offset"],[0,2,1,"","serialize"],[0,2,1,"","size"]],"e7awgsw.sequencercmd.FeedbackCalcOnClassificationCmdErr":[[0,2,1,"","__init__"],[0,4,1,"","read_err"]],"e7awgsw.sequencercmd.SequencerCmd":[[0,3,1,"","MAX_CMD_NO"],[0,2,1,"","__init__"],[0,4,1,"","cmd_id"],[0,4,1,"","cmd_no"],[0,2,1,"","serialize"],[0,2,1,"","size"],[0,4,1,"","stop_seq"]],"e7awgsw.sequencercmd.SequencerCmdErr":[[0,2,1,"","__init__"],[0,4,1,"","cmd_id"],[0,4,1,"","cmd_no"],[0,4,1,"","is_terminated"]],"e7awgsw.sequencercmd.WaveSequenceSetCmd":[[0,3,1,"","ID"],[0,2,1,"","__init__"],[0,4,1,"","awg_id_list"],[0,4,1,"","feedback_channel_id"],[0,4,1,"","key_table"],[0,2,1,"","serialize"],[0,2,1,"","size"]],"e7awgsw.sequencercmd.WaveSequenceSetCmdErr":[[0,2,1,"","__init__"],[0,4,1,"","read_err"],[0,4,1,"","write_err"]],"e7awgsw.utiltool":[[0,6,1,"","plot_graph"],[0,6,1,"","plot_samples"]],"e7awgsw.wavesequence":[[0,1,1,"","WaveChunk"],[0,1,1,"","WaveData"],[0,1,1,"","WaveSequence"]],"e7awgsw.wavesequence.WaveChunk":[[0,2,1,"","__init__"],[0,4,1,"","num_blank_samples"],[0,4,1,"","num_blank_words"],[0,4,1,"","num_repeats"],[0,4,1,"","num_samples"],[0,4,1,"","num_wave_samples"],[0,4,1,"","num_wave_words"],[0,4,1,"","num_words"],[0,4,1,"","wave_data"]],"e7awgsw.wavesequence.WaveData":[[0,2,1,"","__init__"],[0,2,1,"","deserialize"],[0,4,1,"","num_bytes"],[0,4,1,"","num_samples"],[0,2,1,"","sample"],[0,4,1,"","samples"],[0,2,1,"","serialize"]],"e7awgsw.wavesequence.WaveSequence":[[0,3,1,"","MAX_CHUNKS"],[0,3,1,"","MAX_CHUNK_REPEATS"],[0,3,1,"","MAX_POST_BLANK_LEN"],[0,3,1,"","MAX_SEQUENCE_REPEATS"],[0,3,1,"","MAX_WAIT_WORDS"],[0,3,1,"","NUM_SAMPLES_IN_AWG_WORD"],[0,3,1,"","NUM_SAMPLES_IN_WAVE_BLOCK"],[0,2,1,"","__init__"],[0,2,1,"","add_chunk"],[0,2,1,"","all_samples"],[0,2,1,"","all_samples_lazy"],[0,2,1,"","chunk"],[0,4,1,"","chunk_list"],[0,2,1,"","del_chunk"],[0,4,1,"","num_all_samples"],[0,4,1,"","num_all_words"],[0,4,1,"","num_chunks"],[0,4,1,"","num_repeats"],[0,4,1,"","num_wait_samples"],[0,4,1,"","num_wait_words"],[0,2,1,"","save_as_text"]],e7awgsw:[[0,0,0,"-","awgctrl"],[0,0,0,"-","awgwave"],[0,0,0,"-","capturectrl"],[0,0,0,"-","captureparam"],[0,0,0,"-","exception"],[0,0,0,"-","hwdefs"],[1,0,0,"-","labrad"],[0,0,0,"-","lock"],[0,0,0,"-","sequencer"],[0,0,0,"-","sequencercmd"],[0,0,0,"-","utiltool"],[0,0,0,"-","wavesequence"]]},objnames:{"0":["py","module","Python \u30e2\u30b8\u30e5\u30fc\u30eb"],"1":["py","class","Python \u30af\u30e9\u30b9"],"2":["py","method","Python \u30e1\u30bd\u30c3\u30c9"],"3":["py","attribute","Python \u306e\u5c5e\u6027"],"4":["py","property","Python \u30d7\u30ed\u30d1\u30c6\u30a3"],"5":["py","exception","Python \u4f8b\u5916"],"6":["py","function","Python \u306e\u95a2\u6570"]},objtypes:{"0":"py:module","1":"py:class","2":"py:method","3":"py:attribute","4":"py:property","5":"py:exception","6":"py:function"},terms:{"#b":0,"'#":0,"')":[0,1],"',":1,"'awg":1,"'sample":0,"(\u2267":0,"(coef":0,"(i":0,"(int":0,"))":0,").":0,"):":0,")>":[0,1],"*awg":0,"*capmod":0,"*capture":0,"*dsp":0,"*include":0,", stop":0,"--":[0,1],"->":0,".)":0,".awgcapture":[0,3],".awgctrl":[1,2,3],".awgctrlbase":[0,1],".awgwave":[2,3],".capture":0,".capturectrl":[1,2,3],".capturectrlbase":[0,1],".captureparam":[2,3],".client":1,".comp":0,".dicision":0,".dsp":0,".enum":0,".exception":[2,3],".float":0,".futures":1,".hwdefs":[2,3],".intenum":0,".labrad":[0,3],".lock":[2,3],".logger":[0,1],".num":0,".parameterizedwave":0,".post":0,".real":0,".remoteawgctrl":[0,3],".remotecapturectrl":[0,3],".sequencer":[2,3],".sequencercmd":[2,3],".sequencercmderr":0,".sequencerctrlbase":0,".server":1,".sum":0,".threadedserver":1,".threadpoolexecutor":1,".u":0,".utiltool":[2,3],".wavesequence":[2,3],"/\u79d2":0,"/q":0,"0j":0,"0x":0,"2bytes":0,"7awgsw":2,"7fffffff":0,"= (":0,"=<":[0,1],"=[":0,"=false":0,"=feedbackchannel":0,"=true":[0,1],">,":0,">]":0,"\u300d\u300c":0,"\u3042\u3063":0,"\u3042\u308a":0,"\u3042\u308b":0,"\u3044\u308b":0,"\u304a\u3088\u3073":0,"\u304a\u308a":0,"\u304b\u3069\u3046":0,"\u304b\u3089":0,"\u304c\u304f\u308b":0,"\u3053\u3053":0,"\u3053\u3068":[0,1],"\u3053\u306e":[0,1],"\u3053\u308c":0,"\u3054\u3068":0,"\u3059\u3079":0,"\u3059\u308b":[0,1],"\u305a\u3064\u5e83\u304c\u308b":0,"\u305a\u308c\u308b":0,"\u305b\u308b":0,"\u305b\u308c":0,"\u305d\u3046":[0,1],"\u305d\u306e":0,"\u305f\u3044":0,"\u305f\u3059\u3079\u3066":[0,1],"\u305f\u3073":0,"\u305f\u3081":[0,1],"\u3064\u3082":0,"\u3067\u304d":0,"\u3068\u3044\u3046":0,"\u3068\u304d":0,"\u3068\u3057":0,"\u3068\u3057\u3066":0,"\u3069\u306e":0,"\u306a\u3044":[0,1],"\u306a\u304b\u3063":0,"\u306a\u304f":0,"\u306a\u3051\u308c":0,"\u306a\u3057":0,"\u306a\u3063":0,"\u306a\u3089":0,"\u306a\u308b":0,"\u306b\u3088\u3089":0,"\u306b\u3088\u308b":[0,1],"\u306b\u5bfe\u5fdc":0,"\u306e\u307f":0,"\u306f\u307e\u3068\u3081\u3066":0,"\u307e\u3067":0,"\u307e\u3068\u3081\u3066":0,"\u307e\u307e":0,"\u3082\u3057\u304f":0,"\u3082\u306e":0,"\u3088\u3046":0,"\u3089\u308c":[0,1],"\u308c\u308b":0,"\u3092\u901a\u3057":1,"\u30a2\u30c9\u30ec\u30b9":[0,1],"\u30a2\u30e9\u30a4\u30e1\u30f3\u30c8\u30b5\u30a4\u30ba":0,"\u30a4\u30f3\u30b9\u30bf\u30f3\u30b9":[0,1],"\u30a4\u30f3\u30c7\u30c3\u30af\u30b9":0,"\u30a8\u30e9\u30fc":0,"\u30a8\u30e9\u30fc\u30d5\u30e9\u30b0":0,"\u30a8\u30f3\u30c8\u30ea":0,"\u30aa\u30d5\u30bb\u30c3\u30c8":0,"\u30aa\u30d6\u30b8\u30a7\u30af\u30c8":[0,1],"\u30aa\u30fc\u30d0\u30fc\u30d5\u30ed\u30fc":0,"\u30ab\u30a6\u30f3\u30bf":0,"\u30ab\u30a6\u30f3\u30c8":0,"\u30ac\u30a6\u30b9":0,"\u30ac\u30a6\u30b9\u30d1\u30eb\u30b9":0,"\u30ac\u30a6\u30b9\u30d1\u30eb\u30b9\u30af\u30e9\u30b9":0,"\u30ad\u30e3\u30d7\u30c1\u30b9\u30bf\u30fc\u30c8":0,"\u30ad\u30e3\u30d7\u30c1\u30e3":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30a2\u30c9\u30ec\u30b9":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30a2\u30c9\u30ec\u30b9\u30bb\u30c3\u30c8\u30b3\u30de\u30f3\u30c9":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30b7\u30fc\u30b1\u30f3\u30b9":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30c7\u30a3\u30ec\u30a4":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30c7\u30fc\u30bf":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30d1\u30e9\u30e1\u30fc\u30bf":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30d1\u30e9\u30e1\u30fc\u30bf\u30bb\u30c3\u30c8\u30b3\u30de\u30f3\u30c9":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30d1\u30e9\u30e1\u30fc\u30bf\u30ec\u30b8\u30b9\u30c8\u30ea":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30e2\u30b8\u30e5\u30fc\u30eb":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30e6\u30cb\u30c3\u30c8":[0,1],"\u30ad\u30e3\u30d7\u30c1\u30e3\u30e6\u30cb\u30c3\u30c8\u30a8\u30e9\u30fc":0,"\u30ad\u30e3\u30d7\u30c1\u30e3\u30ef\u30fc\u30c9":0,"\u30ad\u30fc":0,"\u30af\u30e9\u30b9":[0,1],"\u30b0\u30e9\u30d5":0,"\u30b3\u30de\u30f3\u30c9":0,"\u30b3\u30de\u30f3\u30c9\u30a8\u30e9\u30fc":0,"\u30b3\u30de\u30f3\u30c9\u30a8\u30e9\u30fc\u30ec\u30dd\u30fc\u30c8":0,"\u30b3\u30de\u30f3\u30c9\u30ad\u30e5\u30fc":0,"\u30b3\u30f3\u30c8\u30ed\u30fc\u30e9":[0,1],"\u30b5\u30a4\u30af\u30eb":0,"\u30b5\u30a4\u30ba":0,"\u30b5\u30f3\u30d7\u30ea\u30f3\u30b0\u30ec\u30fc\u30c8":0,"\u30b5\u30f3\u30d7\u30eb":0,"\u30b5\u30f3\u30d7\u30eb\u30c7\u30fc\u30bf":0,"\u30b5\u30f3\u30d7\u30eb\u30ea\u30b9\u30c8":0,"\u30b5\u30fc\u30d0":1,"\u30b7\u30fc\u30b1\u30f3\u30b5":0,"\u30b7\u30fc\u30b1\u30f3\u30b5\u30a8\u30e9\u30fc":0,"\u30b7\u30fc\u30b1\u30f3\u30b9":0,"\u30b7\u30fc\u30b1\u30f3\u30b9\u30bb\u30c3\u30c8\u30b3\u30de\u30f3\u30c9":0,"\u30b9\u30bf\u30fc\u30c8":0,"\u30b9\u30bf\u30fc\u30c8\u30b3\u30de\u30f3\u30c9":0,"\u30b9\u30bf\u30fc\u30c8\u30c8\u30ea\u30ac":0,"\u30b9\u30ec\u30c3\u30c9":0,"\u30bb\u30c3\u30c8":0,"\u30bd\u30fc\u30b9":[0,1],"\u30bf\u30a4\u30c8\u30eb":0,"\u30bf\u30a4\u30df\u30f3\u30b0":0,"\u30bf\u30a4\u30e0\u30a2\u30a6\u30c8":0,"\u30bf\u30d7\u30eb":0,"\u30c1\u30a7\u30c3\u30af":0,"\u30c1\u30e3\u30cd\u30eb":0,"\u30c1\u30e3\u30f3\u30af":0,"\u30c6\u30ad\u30b9\u30c8\u30c7\u30fc\u30bf":0,"\u30c7\u30e5\u30fc\u30c6\u30a3":0,"\u30c7\u30fc\u30bf":0,"\u30c7\u30fc\u30bf\u30d5\u30a9\u30fc\u30de\u30c3\u30c8":0,"\u30c8\u30ea\u30ac":0,"\u30ce\u30b3\u30ae\u30ea":0,"\u30d0\u30a4\u30c8":0,"\u30d0\u30a4\u30c8\u30a2\u30c9\u30ec\u30b9\u30aa\u30d5\u30bb\u30c3\u30c8":0,"\u30d0\u30fc\u30b8\u30e7\u30f3":0,"\u30d1\u30b9":0,"\u30d1\u30e9\u30e1\u30fc\u30bf":[0,1],"\u30d3\u30c3\u30c8":0,"\u30d3\u30c3\u30c8\u30a2\u30c9\u30ec\u30b9":0,"\u30d5\u30a1\u30a4\u30eb":0,"\u30d5\u30a1\u30a4\u30eb\u30ed\u30c3\u30af":0,"\u30d5\u30a3\u30eb\u30bf":0,"\u30d5\u30a3\u30fc\u30c9\u30d0\u30c3\u30af":0,"\u30d5\u30a3\u30fc\u30c9\u30d0\u30c3\u30af\u30c1\u30e3\u30cd\u30eb":0,"\u30d5\u30e9\u30b0":0,"\u30d6\u30ed\u30c3\u30af":0,"\u30d6\u30ed\u30c3\u30af\u30ab\u30a6\u30f3\u30c8":0,"\u30d7\u30ed\u30b0\u30e9\u30e0":[0,1],"\u30d7\u30ed\u30bb\u30b9":0,"\u30d9\u30fc\u30b9\u30af\u30e9\u30b9":[0,1],"\u30da\u30fc\u30b8":2,"\u30dd\u30b9\u30c8\u30d6\u30e9\u30f3\u30af":0,"\u30e1\u30bd\u30c3\u30c9":[0,1],"\u30e2\u30b8\u30e5\u30fc\u30eb":[0,1,2],"\u30e6\u30cb\u30c3\u30c8":0,"\u30e6\u30fc\u30b6":[0,1],"\u30e9\u30a4\u30d6\u30e9\u30ea":[0,1],"\u30e9\u30d9\u30eb":0,"\u30ea\u30b9\u30c8":0,"\u30ea\u30bb\u30c3\u30c8":0,"\u30ea\u30bd\u30fc\u30b9":[0,1],"\u30ea\u30d4\u30fc\u30c8":0,"\u30ec\u30b8\u30b9\u30c8\u30ea":0,"\u30ec\u30b8\u30b9\u30c8\u30ea\u30ad\u30fc":0,"\u30ec\u30dd\u30fc\u30c8":0,"\u30ed\u30b0":[0,1],"\u30ef\u30fc\u30c9":0,"\u4e0b\u3052\u308b":0,"\u4e0d\u6574\u5408":0,"\u4e26\u3079":0,"\u4e2d\u592e":0,"\u4ed6\u53ef":0,"\u4ed8\u304f":0,"\u4ed8\u3051":[0,1],"\u4ee5\u4e0a":0,"\u4ee5\u4e0b":0,"\u4f4d\u76f8":0,"\u4f4d\u7f6e":0,"\u4f5c\u3089":0,"\u4f7f\u3046":0,"\u4f7f\u3048":0,"\u4f7f\u7528":0,"\u4f8b\u5916":0,"\u4fc2\u6570":0,"\u4fdd\u5b58":0,"\u4fdd\u6301":0,"\u4fe1\u53f7":0,"\u500b\u6570":0,"\u500d\u6570":0,"\u500d\u7cbe":0,"\u5024\u8a08":0,"\u505c\u6b62":0,"\u5148\u982d":0,"\u5165\u529b":0,"\u5168\u3066":0,"\u5168\u5217":0,"\u5168\u6ce2":0,"\u5168\u7dcf":0,"\u5168\u8981":0,"\u5177\u5408":0,"\u51e6\u7406":0,"\u51fa\u529b":[0,1],"\u5206\u306e":0,"\u5207\u308a":1,"\u5217\u6319":0,"\u5217\u6319\u5b50":0,"\u521d\u671f\u5316":0,"\u5224\u5225":0,"\u5224\u5b9a":0,"\u5224\u5b9a\u5f0f":0,"\u5225\u5f0f":0,"\u5236\u5fa1":[0,1],"\u524a\u9664":0,"\u524d\u56de":0,"\u5272\u308a":[0,1],"\u52d5\u5c0f":0,"\u5316\u51e6":0,"\u5316\u5224":0,"\u5316\u7d50":0,"\u533a\u9593":0,"\u5341\u5206":0,"\u5358\u4f4d":0,"\u53c2\u7167":0,"\u53d6\u5f97":0,"\u53d7\u4fe1":0,"\u53e4\u3044":0,"\u53ef\u80fd":0,"\u5404\u8981":0,"\u5408\u308f\u305b":0,"\u540c\u3058":0,"\u540c\u6642":0,"\u542b\u307e":0,"\u542b\u307e\u308c\u308b":0,"\u542b\u3080":0,"\u5468\u6ce2\u6570":0,"\u547c\u3073\u51fa\u3059":0,"\u547c\u3076":[0,1],"\u547c\u3093":0,"\u554f\u308f":0,"\u56db\u5024":0,"\u56db\u5024\u5316":0,"\u56de\u547c":0,"\u56de\u6570":0,"\u5834\u5408":[0,1],"\u5834\u6240":0,"\u5909\u63db":0,"\u5916\u308c\u308b":0,"\u5931\u6557":0,"\u59cb\u3081":0,"\u59cb\u3081\u308b":0,"\u5b8c\u4e86":0,"\u5b9a\u6570":0,"\u5b9f\u6570":0,"\u5b9f\u884c":0,"\u5bfe\u51e6":0,"\u5bfe\u5fdc":0,"\u5bfe\u8c61":[0,1],"\u5c02\u7528":0,"\u5de6\u53f3":0,"\u5e83\u304c\u308a":0,"\u5ea6\u6d6e":0,"\u5f15\u6570":0,"\u5f37\u5236":0,"\u5f53\u305f\u308a":0,"\u5f53\u3066":[0,1],"\u5f62\u90e8":0,"\u5f85\u305f":0,"\u5f85\u3063":0,"\u5f85\u3064":0,"\u5f8c\u51e6":[0,1],"\u5f93\u3046":0,"\u5fc5\u8981":[0,1],"\u5fdc\u3058":0,"\u60c5\u5831":0,"\u6210\u5206":0,"\u6210\u529f":0,"\u623b\u308a\u5024":0,"\u623b\u308b":0,"\u6295\u3052\u308b":0,"\u6301\u3064":0,"\u6307\u5b9a":0,"\u6319\u5b50":0,"\u632f\u5e45":0,"\u639b\u3051\u308b":0,"\u63a5\u7d9a":1,"\u63cf\u753b":0,"\u6570\u3048\u308b":0,"\u6570\u70b9":0,"\u6574\u6570":0,"\u6587\u5b57\u5217":0,"\u65b9\u5f62":0,"\u65b9\u5f62\u6ce2":0,"\u660e\u793a":[0,1],"\u6642\u523b":0,"\u6642\u70b9":0,"\u66f4\u65b0":0,"\u66f8\u304d":0,"\u66f8\u304d\u8fbc\u307f":0,"\u6700\u5927":0,"\u6700\u5c0f\u5024":0,"\u6709\u52b9":[0,1],"\u6709\u52b9\u5316":0,"\u6709\u6ce2":0,"\u671f\u5316":0,"\u672a\u5b9f":0,"\u672a\u5b9f\u88c5":0,"\u672a\u9001":0,"\u672a\u9001\u4fe1":0,"\u672b\u5c3e":0,"\u672c\u6765":0,"\u6761\u4ef6":0,"\u6765\u308b":0,"\u679c\u5358":0,"\u683c\u7d0d":0,"\u691c\u7d22":2,"\u69cb\u6587":[0,1],"\u6a19\u6e96":[0,1],"\u6a2a\u8ef8":0,"\u6a5f\u80fd":[0,1],"\u6b62\u3081\u308b":0,"\u6b63\u5f26\u6ce2":0,"\u6b8b\u3063":0,"\u6c42\u307e\u308b":0,"\u6ce2\u5f62":0,"\u6ce8\u610f":0,"\u6d88\u3048\u308b":0,"\u6e08\u307f":0,"\u6e80\u305f":0,"\u7121\u304b\u3063":0,"\u7121\u52b9":[0,1],"\u7121\u52b9\u5316":0,"\u7121\u95a2\u4fc2":0,"\u7279\u306b":0,"\u7279\u5b9a":0,"\u72ec\u81ea":[0,1],"\u73fe\u5728":0,"\u751f\u6210":0,"\u7528\u3044\u308b":[0,1],"\u7528\u5b9f":0,"\u756a\u53f7":0,"\u756a\u76ee":0,"\u767a\u751f":0,"\u767b\u9332":0,"\u767b\u9332\u5148":0,"\u767b\u9332\u6570":0,"\u767b\u9332\u6e08\u307f":0,"\u767b\u9332\u9806":0,"\u76ee\u7684":0,"\u76f4\u63a5":0,"\u78ba\u8a8d":0,"\u793a\u3059":0,"\u7a2e\u985e":0,"\u7a4d\u7b97":0,"\u7a7a\u304d":0,"\u7a93\u95a2":0,"\u7a93\u95a2\u6570":0,"\u7b26\u53f7":0,"\u7b97\u51fa":0,"\u7ba1\u7406":0,"\u7bc4\u56f2":0,"\u7d22\u5f15":2,"\u7d42\u4e86":[0,1],"\u7d44\u307f\u5408\u308f\u305b":0,"\u7d4c\u904e":0,"\u7d50\u679c":0,"\u7d71\u5408":0,"\u7d9a\u304f":0,"\u7dcf\u548c":0,"\u7e70\u308a\u8fd4\u3057":0,"\u7e70\u308a\u8fd4\u3059":0,"\u865a\u6570":0,"\u884c\u3046":0,"\u884c\u308f":0,"\u8868\u3055":0,"\u8868\u3059":0,"\u8868\u305b\u308b":0,"\u8907\u6570":0,"\u8907\u7d20":0,"\u8981\u7d20":0,"\u8a08\u7b97":0,"\u8a2d\u5b9a":0,"\u8a55\u4fa1":0,"\u8aad\u307f":0,"\u8aad\u307f\u51fa\u3057":0,"\u8abf\u3079\u308b":0,"\u8d77\u3053\u3057":0,"\u8d77\u3053\u3059":0,"\u8db3\u308a":0,"\u8fd4\u3059":0,"\u8ffd\u52a0":0,"\u9001\u4fe1":0,"\u9014\u4e2d":0,"\u9032\u6570":0,"\u9045\u5ef6":0,"\u9078\u629e":0,"\u90e8\u5206":0,"\u9577\u3055":0,"\u958b\u59cb":0,"\u958b\u653e":[0,1],"\u9593\u5185":0,"\u9593\u5f15\u304d":0,"\u9593\u5f15\u304d\u5f8c":0,"\u9593\u6392":0,"\u9593\u9577":0,"\u95a2\u6570":0,"\u95a2\u9023":[0,1],"\u9664\u304f":0,"\u9802\u70b9":0,"\u9806\u756a":0,"\u9818\u57df":0,"abstract":0,"byte":0,"class":[0,1],"const":0,"default":1,"enum":0,"false":[0,1],"float":0,"for":1,"if":1,"in":1,"int":0,"new":1,"package":[0,3],"return":1,"true":[0,1],"with":[0,1],"{awg":0,"{captureunit":0,"{int":0,__:[0,1],_a:0,_adc:0,_addr:[0,1],_alignment:0,_all:0,_args:0,_as:0,_awg:[0,1],_awgctrl:1,_awgs:[0,1],_b:0,_bit:0,_blank:0,_block:[0,1],_bytes:0,_c:0,_capture:[0,1],_capturectrl:1,_captured:[0,1],_channel:0,_chunk:0,_chunks:0,_classification:[0,1],_cmd:0,_coef:0,_coefs:0,_commands:0,_complex:0,_complexw:0,_const:0,_ctrl:1,_cycle:0,_cycles:0,_data:[0,1],_decision:0,_delay:0,_dsp:0,_elems:0,_enable:0,_enabled:0,_end:0,_entries:0,_err:[0,1],_ffffffff:0,_fifo:0,_fir:0,_flag:0,_flags:[0,1],_for:[0,1],_format:0,_free:0,_func:0,_graph:0,_hex:0,_i:0,_id:[0,1],_in:0,_init:[0,1],_integ:0,_interval:0,_ip:1,_iq:0,_label:0,_lazy:0,_len:0,_lib:[0,1],_list:[0,1],_log:[0,1],_mem:0,_module:[0,1],_no:0,_offset:0,_overflow:0,_param:0,_params:[0,1],_pos:0,_post:0,_process:0,_q:0,_range:0,_rate:0,_rd:0,_real:0,_registry:0,_repeats:0,_report:0,_reports:0,_required:0,_results:[0,1],_sample:0,_samples:[0,1],_section:0,_sections:0,_sel:0,_seq:[0,1],_sequence:[0,1],_sequencer:0,_sequences:0,_server:[0,3],_shortage:0,_size:0,_space:0,_start:[0,1],_startable:[0,1],_stop:[0,1],_succeeded:0,_sum:0,_suquencer:0,_table:0,_target:0,_terminated:0,_text:0,_time:0,_timing:[0,1],_to:[0,1],_trigger:[0,1],_unit:[0,1],_units:[0,1],_unprocessed:0,_unsent:0,_val:0,_version:1,_wait:0,_wave:[0,1],_window:0,_word:0,_words:0,_wr:0,accessing:1,acquire:0,adc:0,add:0,addition:1,addr:0,all:0,amplitude:0,and:1,at:1,awg:[0,1],awgcaptureserver:1,awgctrl:0,awgctrlbase:0,awgerr:0,awgstartcmd:0,awgstartcmderr:0,awgtimeouterror:0,be:1,bits:0,bool:[0,1],bytes:0,calc:0,capmod:0,capture:[0,1],captureaddrsetcmd:0,captureaddrsetcmderr:0,capturectrl:0,capturectrlbase:0,captureendfencecmd:0,captureendfencecmderr:0,captureerr:0,capturemodule:0,captureparam:0,captureparamelem:0,captureparamsetcmd:0,captureparamsetcmderr:0,captureunit:0,captureunitaddr:0,captureunittimeouterror:0,check:[0,1],chunk:0,classification:0,classmethod:0,clear:[0,1],close:0,cmd:0,coef:0,color:0,comp:0,complex:0,concurrent:1,convert:0,create:1,crest:0,data:0,decimation:0,decisionfunc:0,del:0,deserialize:0,dicision:0,dict:0,disable:[0,1],discard:[0,1],disconnect:1,dsp:0,dspunit:0,duration:0,duty:0,elem:0,enable:[0,1],end:0,err:0,exception:0,executed:1,fb:0,feedback:0,feedbackcalconclassificationcmd:0,feedbackcalconclassificationcmderr:0,feedbackchannel:0,filepath:0,fir:0,floar:0,frequency:0,from:1,func:0,gaussianpulse:0,gen:0,get:[0,1],handle:1,handling:1,hw:0,hz:0,id:0,idx:0,include:0,includes:0,index:0,initialize:[0,1],initserver:1,instance:1,instead:1,integration:0,interval:[0,1],ip:[0,1],ipaddr:1,iq:0,iqwave:0,is:0,jesd:0,key:0,labrad:1,lifecycle:1,like:1,list:0,localhost:1,logger:[0,1],logging:[0,1],marker:0,max:0,maxes:1,mem:0,methods:1,min:0,module:[2,3],name:1,namespace:[2,3],no:0,none:[0,1],ns:0,nullliblog:[0,1],num:[0,1],numpy:0,object:[0,1],of:[0,1],offset:0,on:1,or:0,other:1,out:1,overflow:0,padding:0,param:[0,1],parameterizedwave:0,phase:0,plot:0,pool:1,pop:0,post:0,property:0,push:0,radian:0,ram:0,reactor:1,read:0,readonly:0,real:0,reentrantfilelock:0,register:0,release:0,remote:1,remoteawgctrl:1,remotecapturectrl:1,request:1,requests:1,reset:[0,1],rgb:0,rturns:0,sample:0,samples:0,sampling:0,save:0,sawtoothwave:0,section:0,sel:0,select:[0,1],self:1,sequencercmd:0,sequencercmderr:0,sequencerctrl:0,sequencerctrlbase:0,sequencererr:0,sequencertimeouterror:0,serialize:0,server:1,set:[0,1],sin:0,sinwave:0,size:0,sof:0,squarewave:0,start:[0,1],stop:0,string:[0,1],subclass:0,submodules:[2,3],subpackages:[2,3],sum:0,synchronous:1,terminate:[0,1],than:1,the:1,thread:1,threaded:1,threadpool:1,threads:1,timeout:[0,1],title:0,to:[0,1],toolittlefreespaceincmdfifoerror:0,tuple:0,twisted:1,type:0,unit:0,use:1,val:0,validate:0,vals:0,value:0,variance:0,version:0,wait:[0,1],warning:[0,1],wave:[0,1],wavechunk:0,wavedata:0,wavesequence:0,wavesequencesetcmd:0,wavesequencesetcmderr:0,which:1,will:1,words:0,write:0},titles:["e7awgsw namespace","e7awgsw.labrad package","e7awg Software Library's documentation","e7awgsw"],titleterms:{"'s":2,".awgcapture":1,".awgctrl":0,".awgwave":0,".capturectrl":0,".captureparam":0,".exception":0,".hwdefs":0,".labrad":1,".lock":0,".remoteawgctrl":1,".remotecapturectrl":1,".sequencer":0,".sequencercmd":0,".utiltool":0,".wavesequence":0,"7awg":2,"7awgsw":[0,1,3],"package":1,_server:1,and:2,contents:2,documentation:2,indices:2,library:2,module:[0,1],namespace:0,software:2,submodules:[0,1],subpackages:0,tables:2}})