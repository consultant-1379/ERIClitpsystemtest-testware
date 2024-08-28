#! /usr/bin/perl
# Script to draw graphs of memory usage for each process from output of top
# Edit input data path names at line 118, 
# Edit output path names at lines 121, 122 and 123

sub writeGraphToHtmlPage
{
	my $processId = $_[0];
	my $command = $_[1];
	my $user = $_[2];
	my @RESData = @{$_[3]};       
	my @VIRTData = @{$_[4]};
	my $htmlNameDir = $_[5]; 

	$htmlName = $htmlNameDir.$user."_".$command._.$processId.".html";
	open FH,">$htmlName" or die $!;
	
	print FH "<html>\n";
        print FH "\t<head>\n";
        print FH "\t\t<script type=\"text/javascript\" src=\"https://www.google.com/jsapi\"></script>\n";
        print FH "\t\t<script type=\"text/javascript\">\n";
        print FH "\t\t\tgoogle.load(\"visualization\", \"1\", {packages:[\"corechart\"]});\n";

        print FH "\t\t\tgoogle.setOnLoadCallback(drawChart);\n";
        print FH "\t\t\tfunction drawChart() {";
        print FH "\t\t\t\tvar data = google.visualization.arrayToDataTable([\n";
        print FH "\t\t\t\t\t['hour', 'RES', 'VIRT'],\n";

	$sizeOfInputArray = @RESData;

	for(my $index = 0;$index < ($sizeOfInputArray - 1);$index++){
		print FH "\t\t\t\t\t\[$index,$RESData[$index],$VIRTData[$index]\],\n";	
	}
	my $lastElement = $sizeOfInputArray -1;
	print FH "\t\t\t\t\t\[$lastElement,$RESData[$lastElement],$VIRTData[$lastElement]\]\n";
        print FH "\t\t\t\t]);\n\n";

        print FH "\t\t\t\tvar options = {\n";
        print FH "\t\t\t\t\ttitle: 'Memory Usage: Command = $command, User = $user, ProcessId = $processId'\n";
        print FH "\t\t\t\t};\n\n";
        print FH "\t\t\t\tvar chart = new google.visualization.LineChart(document.getElementById('chart_div'));\n";
        print FH "\t\t\t\tchart.draw(data, options);\n";
        print FH "\t\t\t}\n";


        print FH "\t\t</script>\n";
        print FH "\t</head>\n";
        print FH "\t<body>\n";
        print FH "\t\t<div id=\"chart_div\" style=\"width: 1450px; height: 750px;\"></div>\n";
        print FH "\t</body>\n";
        print FH "</html>\n";

	close FH;
        return $htmlName
}

sub createMenuHtmlPage
{
	my $htmlFile = $_[0];
        my $listOfGraphs = @{$_[1]};

	open FH,">$menuHtmlFile" or die $!;

	print FH "<!DOCTYPE html>\n";
	print FH "<html>\n";
	print FH "<head>\n";
	print FH "<base target=\"content\">\n";
	print FH "</head>\n";
	print FH "<body>\n";
	print FH "<ol>\n";
	foreach my $graph(@listOfGraphs){
		$graph =~ /([\w-]+)\.html$/;
		$nameOfGraph = $1;
		print FH "<li><a href=\"$graph\">$nameOfGraph</a></li>\n";	
	}
	print FH "</ol>\n";
	print FH "</body>\n";
	print FH "</html>\n";
	close FH;
}

sub createContainerHtmlPage
{
	my $htmlFile = $_[0];
        my $menuHtmlFile = $_[1];

       	$htmlFile =~ /(.+\/)(\w+)\.html$/;
       	$contentHtmlFile = $1."content.html";

	open FH,">$contentHtmlFile" or die $!;
	print FH "<html>\n";
	print FH "<head>\n";
	print FH "<p>Please click on hyperlinks in left hand frame to observe graphs</p>\n";
	print FH "</head>\n";
	print FH "</html>\n";
	close FH;

	open FH,">$htmlFile" or die $!;
	print FH "<html>\n";
	print FH "<head>\n";
	print FH "<title>Memory Usage for Node</title>\n";
	print FH "</head>\n";

	print FH "<frameset cols=\"300,*\" frameborder=\"0\" border=\"0\" framespacing=\"0\">\n";
	print FH "<frame name=\"menu\" src=\"$menuHtmlFile\" marginheight=\"0\" marginwidth=\"0\" scrolling=\"auto\" noresize name=\"menu\">\n";
	print FH "<frame name=\"content\" src=\"$contentHtmlFile\" marginheight=\"0\" marginwidth=\"0\" scrolling=\"auto\" noresize>\n";

	print FH "<noframes>\n";
	print FH "</noframes>\n";

	print FH "</frameset>\n";
	print FH "</html>\n";

	close FH;
}


my $file = "/home/ruth/SP25/MB.140.longrunning/stats/030613/log_top_MS";


$menuHtmlFile = "/home/ruth/SP25/MB.140.longrunning/stats/030613/graphsMS/menu1.html";
$mainHtmlFile = "/home/ruth/SP25/MB.140.longrunning/stats/030613/graphsMS/main.html";
$graphHtmlName = "/home/ruth/SP25/MB.140.longrunning/stats/030613/graphsMS/";
@listOfGraphs;

@nameOfFileName = split('\/+',$file);
$sizeofArray = @nameOfFileName;
$fileName = $nameOfFileName[$sizeofArray - 1];

open FH,"<$file" or die $!;
@fileContents = <FH>;
close FH;

$ctr = 0;
$startPoint = -1;
$endOfFile = @fileContents;
foreach my $line(@fileContents){
        #if($line =~  /^[a-zA-Z]+\s+[a-zA-Z]+\s+\d+\s+[\d:]+\s+[a-zA-Z]+\s+\d+$/){
	if($line =~  /^\s*PID\s+USER\s+PR/){
		$startPoint = $ctr;
	}
        $ctr++;
}


%RESperProcess;
%VIRTperProcess;
for($index = $startPoint;$index <= $endOfFile;$index++){
	@contentOfLastTop = split('\s+',$fileContents[$index]);
	$size = @contentOfLastTop;
	
        $command = $contentOfLastTop[$size - 1];
	$processId = $contentOfLastTop[$size - 12];
	$user = $contentOfLastTop[$size - 11];

	for($index1 = 0;$index1 < $endOfFile;$index1++){
		if($fileContents[$index1] =~ /$command\s*$/ and $fileContents[$index1] =~ /^\s*$processId\s/){
			@contentOfCurrentTop = split('\s+',$fileContents[$index1]);
			$currentVirt = $contentOfCurrentTop[$size - 8];
			$currentRes = $contentOfCurrentTop[$size - 7];

			if($currentRes =~ /(\d+)([a-zA-Z]+)/){
				$memValue = $1;
				$memUnit = $2;

				if($memUnit =~  /m|M/){
					$currentRes = $memValue * 1000;
				}
				elsif($memUnit =~ /g|G/){
					$currentRes = $memValue * 1000000;
				}
				elsif($memUnit =~ /k|K/){
					$currentRes = $memValue;
				}
			}

			if($currentVirt =~ /(\d+)([a-zA-Z]+)/){
				$memValue = $1;
				$memUnit = $2;

				if($memUnit =~ /m|M/){
					$currentVirt = $memValue * 1000;
				}
				elsif($memUnit =~ /g|G/){
					$currentVirt = $memValue * 1000000;
				}
				elsif($memUnit =~ /k|K/){
					$currentVirt = $memValue;
				}
			}				
			push(@{$RESperProcess{$processId}{$command}{$user}},$currentRes);
			push(@{$VIRTperProcess{$processId}{$command}{$user}},$currentVirt);

		}
	}
}

foreach my $processId(keys %RESperProcess){
	foreach my $command(keys %{$RESperProcess{$processId}}){
		foreach my $user(keys %{$RESperProcess{$processId}{$command}}){
			$sizeOfArray = @{$RESperProcess{$processId}{$command}{$user}};
			if(${$RESperProcess{$processId}{$command}{$user}}[$sizeOfArray - 1] > 0){
	                      push(@listOfGraphs,writeGraphToHtmlPage($processId,$command,$user,\@{$RESperProcess{$processId}{$command}{$user}},\@{$VIRTperProcess{$processId}{$command}{$user}},$graphHtmlName));

			}
		}
	}
}

createMenuHtmlPage($menuHtmlFile,@listOfGraphs);
createContainerHtmlPage($mainHtmlFile,$menuHtmlFile);
