filename = 'samp2.mp3';

[speech,fs] = audioread(filename); %insert song here
if fs ~= 44100
    filename = strrep(filename,'.mp3','.wav');
    audiowrite(filename,speech,44100);
    [speech,fs] = audioread(filename);
end

speech = (speech(:,1)+speech(:,2))/2; % convert from stereo to mono




[length dontcare] = size(speech);

%fm ~= 1400kHz; fs = 44.1kHz -> fs << 2*fm

[length dontcare] = size(speech);
desiredSamp = 30/(1/fs);
speech = speech(round(length/2 - round(desiredSamp/2)) : round(length/2 + (desiredSamp/2)));%grab audio from mmiddle 30 secs
length = 30000; %length of sample in ms
Tw = length/510;
Ts = Tw*.5;
alpha = .95;
M = 22;
L = 22;
window = blackmanharris(32);
R = [22 22000];
N = 22;

[CC,FBE,frames] =mfcc(speech,fs,Tw,Ts,alpha,window,R,M,N,L);

figure('Position', [30 100 800 200], 'PaperPositionMode', 'auto', ... 
                 'color', 'w', 'PaperOrientation', 'landscape', 'Visible', 'on' ); 
      
          imagesc( [1:size(CC,2)], [0:N-1], CC ); 
          axis( 'xy' );
          xlabel( 'Frame index' ); 
          ylabel( 'Cepstrum index' );
          title( 'Mel frequency cepstrum' );