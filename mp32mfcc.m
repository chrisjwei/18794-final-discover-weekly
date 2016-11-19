function CC = mp32mfcc(filename)

    [speech,fs] = audioread(filename); %insert song here

    speech = mean(speech, 2); % convert from stereo to mono
    %fm ~= 1400kHz; fs = 44.1kHz -> fs << 2*fm

    [length ~] = size(speech);
    desiredSamp = 30/(1/fs);
    speech = speech(round(length/2 - round(desiredSamp/2)) : round(length/2 + (desiredSamp/2)));%grab audio from mmiddle 30 secs
    length = 30000; %length of sample in ms
    Tw = length/500;
    Ts = Tw*.5;
    alpha = .95;
    M = 22;
    L = 22;
    window = blackmanharris(32);
    R = [22 22000];
    N = 22;

    [CC,~,~] =mfcc(speech,fs,Tw,Ts,alpha,window,R,M,N,L);
    if size(CC,2) ~= 999
        CC = NaN;
    end
end