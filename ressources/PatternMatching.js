/* This module contain patternMatching functions
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([],function(){ return {
	/* match tw graphs according to specific rules
	 * @input : g1 : the first graph
	 * @input : g2 : the second graph, g1 and g2 must be typed by the same graph
	 * @return a merged graph.
	 */
	match:function(g1,g2){
			var nodeByFst={"g1":{},"g2":{}};
			var nodeEmpty={"g1":[],"g2":[]};
			var nodeByLst={"g1":{},"g2":{}};
			var nodeByType = {"g1":{},"g2":{}};
			var matchByNode = {};
			var edgeBySource = {"g1":{},"g2":{}};
			var edgeByTarget = {"g1":{},"g2":{}};
			var nodeById = {"g1":{},"g2":{}};
			g1.name="g1";
			g2.name="g2";
			//for each graph : generate hashtables
			[g1,g2].forEach(function(g){
				g.edges.forEach(function(edge,idx){
					if(!edgeBySource[g.name][edge.from])edgeBySource[g.name][edge.from] =[];
					edgeBySource[g.name][edge.from].push(idx);
					if(!edgeByTarget[g.name][edge.to])edgeByTarget[g.name][edge.to] =[];
					edgeByTarget[g.name][edge.to].push(idx);
				});
				g.nodes.forEach(function(node,idx){
					if(!nodeByType[g.name][node.type])nodeByType[g.name][node.type]=[];
					nodeByType[g.name][node.type].push(idx);
					nodeById[g.name][node.id]=idx;
				});
				nodeByType[g.name]["Contact"].forEach(function(node){
					if(edgeByTarget[g.name][g.nodes[node].id]){
						edgeByTarget[g.name][g.nodes[node].id].forEach(function(edge){
							var son_id = g.edges[edge].from;
							var son_type = g.nodes[nodeById[g.name][son_id]].type;
							var smpl = son_id.split("_")[0];
							if(son_type == "FirstName"){
								if(!nodeByFst[g.name][smpl])nodeByFst[g.name][smpl]=[];
								nodeByFst[g.name][smpl].push(node);
								g.nodes[node].fst=smpl;
							}if(son_type == "LastName"){
								if(!nodeByLst[g.name][smpl])nodeByLst[g.name][smpl]=[];
								nodeByLst[g.name][smpl].push(node);
								g.nodes[node].lst=smpl;
							}  
						});
					}if(edgeByTarget[g.name][g.nodes[node].id].length<=1){
						nodeEmpty[g.name].push(node);
					}
				});
			});
			console.log("Graph loaded !");
			//first : match people with same name and surname.
			//I assume that two people with same name/surname are the same persone
			for(lst in nodeByLst.g1){
				nodeByLst.g1[lst].forEach(function(node){
					if(nodeByLst["g2"][lst]){
						var possible = nodeByLst["g2"][lst].filter(function(node_id){
							return g2.nodes[node_id].fst == g1.nodes[node].fst;
						});
						if(possible.length == 1){
							matchByNode[node]=[{sc_total:0,id:possible[0]}];
						}else if(possible.length == 0){
							var m =matchFst(node);
							if(m.length>0)
								matchByNode[node]=m;
						}else if(possible.length>1){
							matchByNode[node]=patternMatch(node,possible);
						}
					}else {
						var m =matchFst(node);
						if(m.length>0)
							matchByNode[node]=m;
					}
				})
			};
			nodeEmpty["g1"].forEach(function(n_id){
				var node = g1.nodes[n_id];
				var large_possible = nodeByFst["g2"][node.fst];
				matchByNode[n_id]=patternMatch(n_id,large_possible);
			});
			var resp = geneticAlgo(10000,100,matchByNode);
			var id_match = Object.keys(matchByNode);
			var str="";
			resp.forEach(function(e,i){
				if(e.id!="NAN")
					str+=g1.nodes[id_match[i]].fst+" "+g1.nodes[id_match[i]].lst+"->"+g2.nodes[e.id].fst+" "+g2.nodes[e.id].lst+"\n";
				else
					str+=g1.nodes[id_match[i]].fst+" "+g1.nodes[id_match[i]].lst+"->\n";
			});
			var url = 'data:text/json;charset=utf8,' + encodeURIComponent(str);
			window.open(url, '_blank');			
			var final_match= id_match.map(function(el,i){
				return {id:el,map:resp[i]};
			});
			return toGraph();
			/* return a regraph graph from the mergeAttributes
			 * @return : a regraph graph
			 */
			function toGraph(){
				var ng={edges:[],nodes:[]};
				var to_delete =[];
				final_match.forEach(function(el,i){
					if(el.map.id!="NAN"){
						if(edgeBySource["g2"][g2.nodes[el.map.id].id]){
							edgeBySource["g2"][g2.nodes[el.map.id].id].forEach(function(e_id,i){	
								g2.edges[e_id].from=g1.nodes[el.id].id;
								g1.nodes[el.id].type="Concat";
							});
							delete edgeBySource["g2"][g2.nodes[el.map.id].id];
						}if(edgeByTarget["g2"][g2.nodes[el.map.id].id]){
							edgeByTarget["g2"][g2.nodes[el.map.id].id].forEach(function(e_id,i){
								g2.edges[e_id].to=g1.nodes[el.id].id;
								g1.nodes[el.id].type="Concat";
							});
							delete edgeByTarget["g2"][g2.nodes[el.map.id].id];
						}
						to_delete.push(el.map.id);
					}
				});
				to_delete=to_delete.sort(function(a,b){
					return a>b;
				});
				console.log(to_delete);
				for(var i=to_delete.length-1;i>=0;i--){
					g2.nodes.splice(to_delete[i],1);
				}
				g2.nodes=g2.nodes.map(function(e){
					if(edgeBySource["g2"][e.id]){
						edgeBySource["g2"][e.id].forEach(function(e_id,i){
							g2.edges[e_id].from=e.id+"_"+g2.name;
						});
					}if(edgeByTarget["g2"][e.id]){
						edgeByTarget["g2"][e.id].forEach(function(e_id,i){
							g2.edges[e_id].to=e.id+"_"+g2.name;
						});
					}
					e.id+="_"+g2.name;
					return e;});
				ng.edges=g1.edges.concat(g2.edges);
				ng.nodes = g1.nodes.concat(g2.nodes);
				return ng;
			}
			/* A simple genetic algorithm with mutation and crossover
			 * @input : timeout : the duration of the algorithm
			 * @input : pop_size : the size of the population
			 * @input : map : the original population
			 */
			function geneticAlgo(timeout,pop_size,map){
				var sequences = [];
				var origin = [];
				for(var i=0;i<pop_size;i++){
					var el=genSec(map);
					origin.push(el);
				};
				var map_key = Object.keys(map);
				for(var i=0;i<timeout;i++){
					sequences=copyPop(origin);
					sequences.forEach(function(seq){
						var action=Math.floor((Math.random() * 100));
						if(action>30 && action <65){
							var idx=Math.floor((Math.random() * seq.length));
							seq[idx]=map[map_key[idx]][Math.floor((Math.random() * map[map_key[idx]].length))];		
						}else if(action>=65){
							var idx=Math.floor((Math.random() * seq.length));
							var cross = Math.floor((Math.random() * pop_size));
							var tmp=seq[idx];
							seq[idx]=sequences[cross][idx];
							sequences[cross][idx]=tmp;
						}
					});
					sequences.forEach(function(seq,idx){
						if(totScore(seq)<totScore(origin[idx]) && Math.floor((Math.random() * 100))>49){
							if(viable(seq))
								origin[idx]=seq;
						}else if(totScore(seq)>totScore(origin[idx]) && Math.floor((Math.random() * 100))>80){
							if(viable(seq))
								origin[idx]=seq;
						}
					});
					/*if(i%1000==0)
						console.log(origin.map(totScore));
					*/
				}
				var idx=0;
				var sc0=totScore(origin[0]);
				origin.map(totScore).forEach(function(e,i){
					if(e>sc0){
						sc0=e;
						idx=i;
					}
				});
				return origin[idx];
			}
			/* verify if a sequence is viable
			 * @input : seq : the sequence
			 * @return : boolean : true if viable, false if not.
			 */
			function viable(seq){
				for(var i=0;i<seq.length;i++){
					for(var j=i+1;j<seq.length-1;j++){
						if(seq[i].id == seq[j].id && seq[i].id!="NAN"){
							return false;
						} 
					}
				}
				return true;
			}
			/* return a clone of a population
			 * @input : vect : the originale population
			 * @return : a copy of the population
			 */
			function copyPop(vect){
				var ret=[];
				vect.forEach(function(el){
					ret.push(el.concat());
				});
				return ret;
			}
			/* return the total score of a candidate
			 * @input : seq : the candidate
			 * @return : the total score of the candidate
			 */
			function totScore(seq){
				return seq.reduce(function(accu,el){
					return accu+el.sc_total;
				},0)
			}
			/* create a new candidate from a mapping
			 * @input : the mapping
			 * @return : a new candidate
			 */
			function genSec(map){
				var ret1=[];
				var ret2=[];
				var already_select={};
				var keys = Object.keys(map);
				var seed = Math.floor((Math.random() * keys.length));
				for(var i=seed;i<keys.length;i++){
					ret1.push(selectMaxNotSelected(map[keys[i]],already_select));
				}
				for(var i=0;i<seed;i++){
					ret2.push(selectMaxNotSelected(map[keys[i]],already_select));
				};
				return ret2.concat(ret1);
			};
			/* select the best mapping not selected
			 * randomly select another node not selected
			 * @input : mapping : the used mapping
			 * @input : selected : the already selected nodes
			 * @return : a correct mapping
			 */
			function selectMaxNotSelected(mapping,selected){
				var ret={id:"NAN",sc_total:1000};
				var dtc = Math.floor((Math.random() * 100))<10;
				mapping.forEach(function(elt,i){
					if(!selected[elt.id] && (elt.sc_total<ret.sc_total || dtc))
						ret=elt;
				});
				if(ret.id!="NAN") selected[ret.id]=true;
				return ret;
			};
			/* if we only have a first name, find all compatible contact.
			 * I assume that if there is only one person with the same first name it might be the same
			 * matching check is required
			 * @input : n_id : the node to match for the first name
			 * @return : the possible matchings
			*/
			function matchFst(n_id){
				var node = g1.nodes[n_id];
				var large_possible = nodeByFst["g2"][node.fst].filter(function(id){
					return !g2.nodes[id].lst || g2.nodes[id].lst!=node.lst;
				});
				if(large_possible)
					return patternMatch(n_id,large_possible);
				return [];
			}
			/* return a grade for each possibility according to its matching with the node
			 * @input : n_id : the node id
			 * @input : possibility : the possible nodes in g2
			 * @return : a list of possibilities with grades.
			*/
			function patternMatch(n_id,possibility){
				var orig_pattern = genPattern(n_id,g1);
				var dest_pattern = possibility.map(function(nn){
					return genPattern(nn,g2);
				});
				var hash_fst = {};//get all firstname in the orginal pattern without redundency
				orig_pattern.contact.forEach(function(e){
					hash_fst[g1.nodes[e].fst]=true;
				});
				var orig_ct_fst = Object.keys(hash_fst);
				//add meta_data to each target pattern
				var ret = dest_pattern.map(function(pt){
					//difference between conersations
					var conv_diff = orig_pattern.conv.length-pt.conv.length;
					//difference between contacts
					var cont_diff = orig_pattern.contact.length-pt.contact.length;
					//reduce the target pattern : remove conversation with no matching contact
					var reduced_pattern = reducePattern(pt,orig_ct_fst);
					//difference between conersations in reduced pattern
					var red_conv_diff = orig_pattern.conv.length-reduced_pattern.conv.length;
					//difference between contacts in reduced pattern
					var red_cont_diff = orig_pattern.contact.length-reduced_pattern.contact.length;
					//get the missing contact between original pattern and reduced one
					var contact_of_origin = reduced_pattern.contact.filter(function(ct){
						return orig_ct_fst.indexOf(g2.nodes[ct].fst)!=-1;
					});
					var missing_contact = orig_ct_fst.length-contact_of_origin.length;
					//difference between edges from other contact to conversation 
					var red_edge_diff = orig_pattern.edges_to_cont.length-reduced_pattern.edges_to_cont.length;	
					return {"diff_c":conv_diff,
							"diff_ct":cont_diff,
							"orig_c":orig_pattern.conv.length,
							"orig_ct":orig_pattern.contact.length,
							"r_diff_c":red_conv_diff,
							"r_diff_ct":red_cont_diff,
							"orig_ct_l":orig_ct_fst.length,
							"miss_ct":missing_contact,
							"orig_edge":orig_pattern.edges_to_cont.length,
							"ct_to_cv_diff":red_edge_diff,
							"reduce":reduced_pattern
							};
				});
				//compute score.
				ret = ret.map(score);
				return ret;
			}
			/* calculate a matching score from meta datas
			 * @input : el : a pattern with meta data
			 * @return : a pattern with score
			 */
			function score(el){
				var sc =[];
				if(el.miss_ct<0)
					sc.push(el.miss_ct/(-el.miss_ct+el.orig_ct_l));
				else
					sc.push(el.orig_ct_l!=0?(el.miss_ct/el.orig_ct_l):100);
				if(el.r_diff_ct<0)
					sc.push(el.r_diff_ct/(-el.r_diff_ct+el.orig_ct));
				else
					sc.push(el.orig_ct!=0?(el.r_diff_ct/el.orig_ct):100);
				if(el.r_diff_c<0)
					sc.push(el.r_diff_c/(-el.r_diff_c+el.orig_c));
				else
					sc.push(el.orig_c!=0?(el.r_diff_c/el.orig_c):100);
				if(el.diff_ct<0)
					sc.push(el.diff_ct/(-el.diff_ct+el.orig_ct));
				else
					sc.push(el.orig_ct!=0?(el.diff_ct/el.orig_ct):100);
				if(el.diff_c<0)
					sc.push(el.diff_c/(-el.diff_c+el.orig_c));
				else
					sc.push(el.orig_c!=0?(el.diff_c/el.orig_c):100);
				if(el.ct_to_cv_diff<0)
					sc.push(el.ct_to_cv_diff/(-el.ct_to_cv_diff+el.orig_edge));
				else
					sc.push(el.orig_edge!=0?(el.ct_to_cv_diff/el.orig_edge):100);
				el.score=sc;
				el.sc_total= (sc[0]<0?sc[0]*1.1:sc[0]*2)
					+(sc[1]<0?sc[1]*1:sc[1]*0.7)
					+(sc[2]<0?sc[2]*0.9:sc[2]*0.6)
					+(sc[3]<0?sc[3]*0.5:sc[3]*0.4)
					+(sc[4]<0?sc[4]*0.4:sc[4]*0.3)
					+(sc[5]<0?sc[5]*0.6:sc[5]*0.5);
				el.id = el.reduce.source;
				return el;
			}
			/* reduce a target pattern according to the original one
			 * @input : pt : the target pattern
			 * @input : orig_ct_fst : the list of contact of the original pattern
			 * @return : a reduced pattern
			 */
			function reducePattern(pt,orig_ct_fst){
				var reduced_conv = pt.conv.filter(function(cv){
					var possible_ct = edgeByTarget["g2"][g2.nodes[cv].id].filter(function(e_id){
						return orig_ct_fst.indexOf(g2.nodes[nodeById["g2"][g2.edges[e_id].from]].fst)!=-1;
					});
					return possible_ct.length>0;
				});
				var reduced_etc = pt.edges_to_conv.filter(function(etc){
					return reduced_conv.indexOf(nodeById["g2"][g2.edges[etc].to])!=-1;
				});
				var reduced_efc = pt.edges_to_cont.filter(function(etc){
					return reduced_conv.indexOf(nodeById["g2"][g2.edges[etc].to])!=-1;
				});
				var hash_ct = {};
				reduced_efc.forEach(function(e_id){
					hash_ct[nodeById["g2"][g2.edges[e_id].from]]=true;
				});
				var reduced_ct = Object.keys(hash_ct);
				return {"source":pt.source,"contact":reduced_ct,"conv":reduced_conv,"edges_to_conv":reduced_etc,"edges_to_cont":reduced_efc};
			}
			/* create the 2-cloture pattern for each node
			 * @input : n_id : the node id
			 * @input : g : the node graph
			 * @return : a list of nodes and edges in the closure
			 */
			function genPattern(n_id,g){
				var node = g.nodes[n_id];
				var ret={"source":n_id,"contact":[],"conv":[],"edges_to_conv":[],"edges_to_cont":[]};
				var ct_hash={};
				var edge_hash={};
				if(edgeBySource[g.name][node.id]){
					edgeBySource[g.name][node.id].forEach(function(e_id){
						var conv = g.edges[e_id].to;
						ret.conv.push(nodeById[g.name][conv]);
						ret.edges_to_conv.push(e_id);
						var speakers_link = edgeByTarget[g.name][conv];
						if(speakers_link){
							speakers_link.forEach(function(e2_id){
								var speaker_node = g.edges[e2_id].from;
								if(nodeById[g.name][speaker_node]!=n_id){
									if(!ct_hash[nodeById[g.name][speaker_node]]){
										ct_hash[nodeById[g.name][speaker_node]]=true;
										ret.contact.push(nodeById[g.name][speaker_node]);
									}
									if(!edge_hash[e2_id]){
										edge_hash[e2_id]=true;
										ret.edges_to_cont.push(e2_id);
									}
								}
							});
						}
					})
				}
				return ret;
			}
	}
}});