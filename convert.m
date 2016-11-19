genre_ids = [18 1153 100007 17 15 6 20 14 21];
max_bytes = 12000000; %12mb
min_bytes = 1000000;
num_windows = 999;

for genre_id = genre_ids
    sprintf('starting genre_id = %d', genre_id)
    files = dir(sprintf('scraper\\clips\\%d\\*.mp3', genre_id));
    filesizes = extractfield(files, 'bytes');
    files = files(filesizes < max_bytes & filesizes > min_bytes);
    [num_files, ~] = size(files);
    sprintf('converting %d files', num_files);
    filenames = extractfield(files, 'name');
    X = zeros(num_files, 22*num_windows);
    y = ones(num_files, 1) * genre_id;
    for i = 1:num_files
        filename = char(filenames(i));
        sprintf('converting (%d/%d) %s', i, num_files, filename)
        cc = mp32mfcc(sprintf('scraper\\clips\\%d\\%s',genre_id, filename));
        if isnan(cc)
            sprintf('invalid CC')
            X(i,:) = NaN;
        else
            X(i,:) = reshape(cc, 1, 22*num_windows);
        end
    end
    sprintf('saving results')
    save(sprintf('%d', genre_id), 'X', 'y');
end